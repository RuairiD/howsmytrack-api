from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from howsmytrack.core.models import MediaTypeChoice


# TODO specific error messages for each supported platform, including instructions on how to obtain the correct links.
# Part of this can be achieved by passing back an `invalid_media_url` field which, when true, causes the client to show
# formatted instructions and perhaps an informational modal.
INVALID_MEDIA_URL_MESSAGE = "Please provide any of the following: a valid Soundcloud URL of the form `https://soundcloud.com/artist/track` (or `https://soundcloud.com/artist/track/secret` for private tracks), a shareable Google Drive URL of the form `https://drive.google.com/file/d/abcdefghijklmnopqrstuvwxyz1234567/view`, a Dropbox URL of the form `https://www.dropbox.com/s/abcdefghijklmno/filename` or a OneDrive URL of the form `https://onedrive.live.com/?authkey=AUTHKEY&cid=CID&id=ID`"


ONEDRIVE_DOWNLOAD_PARTS = [
    "https://onedrive.live.com/download",
    "authkey=",
    "cid=",
    "resid=",
]
ONEDRIVE_FILE_PARTS = [
    "https://onedrive.live.com/",
    "authkey=",
    "cid=",
    "id=",
]


def is_onedrive_url(media_url):
    # Directly downloadable URLs are used for OneDrive links.
    # If the user provides this directly, great. Otherwise, we can
    # still assemble the link from the regular file URL.
    # We cannot do anything with a OneDrive shortlink from the
    # Share menu and should reject it.
    return all([url_part in media_url for url_part in ONEDRIVE_DOWNLOAD_PARTS]) or all(
        [url_part in media_url for url_part in ONEDRIVE_FILE_PARTS]
    )


def validate_media_url(media_url):
    url_validator = URLValidator()
    try:
        url_validator(media_url)
    except ValidationError:
        raise ValidationError(message=INVALID_MEDIA_URL_MESSAGE,)
    if "https://soundcloud.com/" in media_url:
        return MediaTypeChoice.SOUNDCLOUD.name
    if "dropbox.com/" in media_url:
        return MediaTypeChoice.DROPBOX.name
    if "drive.google.com/file" in media_url:
        return MediaTypeChoice.GOOGLEDRIVE.name
    if is_onedrive_url(media_url):
        return MediaTypeChoice.ONEDRIVE.name
    raise ValidationError(message=INVALID_MEDIA_URL_MESSAGE,)
