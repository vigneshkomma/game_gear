from .models import Profile


def get_profile(user):
    """Fetch this user's Profile, creating one if it doesn't exist yet.

    request.user.profile assumes the post_save signal in models.py
    already ran — true for anyone who signed up through signup_view,
    but NOT for a user created any other way (createsuperuser, the
    admin site, a data import, or any user that existed before the
    signal was added to the codebase). For those, .profile raises
    RelatedObjectDoesNotExist.

    Every view in every app that needs "the current user's profile"
    should call this instead of touching request.user.profile
    directly — that's what makes the whole site self-healing instead
    of 500ing for any user without a Profile row.
    """
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile