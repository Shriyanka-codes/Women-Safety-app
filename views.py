from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import json

# ── Twilio SMS helper ──────────────────────────────────────────────
def _send_sms(to_number, body):
    """Send an SMS via Twilio. Returns True on success, False on failure."""
    try:
        from twilio.rest import Client as TwilioClient
        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_number,
        )
        return True
    except Exception as exc:
        print(f'[Twilio] SMS to {to_number} failed: {exc}')
        return False

from .models import (
    Report, EmergencyContact, SOSAlert, SOSLog,
    Notification, HelpCenter, UserProfile
)
from .forms import UserProfileForm


# ─────────────────────────────────────────────
# Home
# ─────────────────────────────────────────────

def home(request):
    return render(request, 'home.html')


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip().lower()
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        messages.success(request, 'Registered and logged in successfully.')
        return redirect('home')

    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip().lower()
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ─────────────────────────────────────────────
# Emergency Contacts
# ─────────────────────────────────────────────

@login_required
def manage_contacts(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        update_id = request.POST.get('update_id')

        if update_id:
            contact = get_object_or_404(EmergencyContact, id=update_id, user=request.user)
            contact.name = name
            contact.phone_number = phone
            contact.email = email
            contact.save()
        else:
            EmergencyContact.objects.create(
                user=request.user, name=name, phone_number=phone, email=email
            )
        return redirect('manage_contacts')

    contacts = EmergencyContact.objects.filter(user=request.user)
    edit_id = request.GET.get('edit')
    edit_contact = None
    if edit_id:
        edit_contact = get_object_or_404(EmergencyContact, id=edit_id, user=request.user)

    return render(request, 'contacts.html', {
        'contacts': contacts,
        'edit_contact': edit_contact,
    })


@login_required
def delete_contact(request, id):
    contact = get_object_or_404(EmergencyContact, id=id, user=request.user)
    contact.delete()
    return redirect('manage_contacts')


# ─────────────────────────────────────────────
# SOS Alert  ← Main feature
# ─────────────────────────────────────────────

@login_required
def trigger_sos(request):
    """
    POST (JSON): { latitude, longitude }
    Sends an HTML email with a Google Maps link to all saved emergency contacts.
    Returns JSON so the frontend can react without a page reload.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, Exception):
            # Fallback: try form-encoded data
            data = request.POST

        lat = data.get('latitude')
        lon = data.get('longitude')

        if not lat or not lon:
            return JsonResponse({'status': 'error', 'msg': 'Location data missing.'}, status=400)

        lat = float(lat)
        lon = float(lon)

        # Save the SOS log
        SOSLog.objects.create(
            user=request.user,
            message='🚨 SOS triggered via button',
            latitude=lat,
            longitude=lon,
        )

        # Also save to SOSAlert
        alert = SOSAlert.objects.create(
            user=request.user,
            latitude=lat,
            longitude=lon,
        )

        # Fetch all emergency contacts
        contacts = EmergencyContact.objects.filter(user=request.user)
        recipient_list = [c.email for c in contacts if c.email]

        if not recipient_list:
            return JsonResponse({
                'status': 'warning',
                'msg': 'SOS recorded but you have no emergency contacts saved!'
            })

        # Build Google Maps link
        maps_link = f"https://www.google.com/maps?q={lat},{lon}"

        # Prepare email
        subject = '🚨 URGENT: SOS Alert from Women Safety App'
        context = {
            'username': request.user.username,
            'lat': lat,
            'lon': lon,
            'maps_link': maps_link,
        }
        html_content = render_to_string('sos_email.html', context)
        plain_text = (
            f"🚨 URGENT SOS ALERT\n\n"
            f"{request.user.username} needs immediate help!\n\n"
            f"Live Location: {maps_link}\n\n"
            f"Please respond immediately!"
        )

        # Send to all contacts
        sent_count = 0
        for recipient_email in recipient_list:
            try:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient_email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                sent_count += 1
            except Exception as e:
                print(f"Failed to send email to {recipient_email}: {e}")

        alert.sent = (sent_count > 0)
        alert.save()

        # ── Twilio SMS ─────────────────────────────────────────────────
        sms_sent = 0
        sms_failed = 0
        if getattr(settings, 'TWILIO_ENABLED', False):
            sms_body = (
                f'\U0001f6a8 URGENT SOS ALERT!\n\n'
                f'{request.user.get_full_name() or request.user.username} needs immediate help!\n\n'
                f'Live Location:\n{maps_link}\n\n'
                f'Please respond ASAP or call emergency services!'
            )
            phone_contacts = [c for c in contacts if c.phone_number]
            for contact in phone_contacts:
                phone = contact.phone_number.strip()
                # Ensure E.164 format — add +91 if no country code
                if not phone.startswith('+'):
                    phone = '+91' + phone.lstrip('0')
                if _send_sms(phone, sms_body):
                    sms_sent += 1
                else:
                    sms_failed += 1

        return JsonResponse({
            'status': 'success',
            'msg': f'SOS alert sent to {sent_count} contact(s)!',
            'sent_count': sent_count,
            'sms_sent': sms_sent,
            'twilio_enabled': getattr(settings, 'TWILIO_ENABLED', False),
        })

    # GET: show the SOS page
    contacts = EmergencyContact.objects.filter(user=request.user)
    return render(request, 'send_sos.html', {'contacts': contacts})


# ─────────────────────────────────────────────
# Report (legacy — kept for compatibility)
# ─────────────────────────────────────────────

@login_required
def report_view(request):
    return redirect('trigger_sos')


# ─────────────────────────────────────────────
# Notifications
# ─────────────────────────────────────────────

@login_required
def notifications_view(request):
    notifs = request.user.notifications.order_by('-timestamp')
    return render(request, 'notifications.html', {'notifications': notifs})


# ─────────────────────────────────────────────
# Map / Help Centers
# ─────────────────────────────────────────────

def map_view(request):
    help_centers = HelpCenter.objects.all()
    centers_data = [
        {
            'name': center.name,
            'lat': center.latitude,
            'lon': center.longitude,
            'address': center.address,
        }
        for center in help_centers
    ]
    return render(request, 'map.html', {'help_centers': centers_data})


# ─────────────────────────────────────────────
# Profile
# ─────────────────────────────────────────────

@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'profile.html', {'profile': profile})


@login_required
def edit_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'edit_profile.html', {'form': form})


# ─────────────────────────────────────────────
# Blog / Legal Info
# ─────────────────────────────────────────────

@login_required
def blog_legal_info(request):
    return render(request, 'blog_legal_info.html')
