import logging
import re

import cloudinary.utils
import requests

logger = logging.getLogger(__name__)

TRANSFORMATION_PREFIXES = (
    'fl_', 't_', 'a_', 'b_', 'c_', 'e_', 'g_', 'h_', 'l_', 'o_', 'r_', 'u_', 'w_', 'x_', 'y_', 'z_',
)


def _cloudinary_parts(cv_url):
    if not cv_url or 'cloudinary.com' not in cv_url:
        return None

    match = re.search(r'/([^/]+)/(image|raw|video)/upload/(.+)$', cv_url)
    if not match:
        return None

    resource_type = match.group(2)
    path = match.group(3).split('?')[0]
    segments = [segment for segment in path.split('/') if segment]

    if segments and segments[0].startswith('v') and segments[0][1:].isdigit():
        segments = segments[1:]

    while segments and (',' in segments[0] or segments[0].startswith(TRANSFORMATION_PREFIXES)):
        segments = segments[1:]

    if not segments:
        return None

    public_id_with_ext = '/'.join(segments)
    public_id = public_id_with_ext
    if '.' in public_id_with_ext.rsplit('/', 1)[-1]:
        public_id = public_id_with_ext.rsplit('.', 1)[0]

    return {
        'resource_type': resource_type,
        'public_id': public_id,
    }


def resolve_cv_view_url(cv_url):
    if not cv_url:
        return ''

    parts = _cloudinary_parts(cv_url)
    if not parts:
        return cv_url

    try:
        signed_url, _ = cloudinary.utils.cloudinary_url(
            parts['public_id'],
            resource_type=parts['resource_type'],
            sign_url=True,
            secure=True,
            type='upload',
        )
        return signed_url or cv_url
    except Exception as error:
        logger.warning('Could not sign Cloudinary CV URL: %s', error)
        return cv_url


def fetch_cv_bytes(cv_url):
    candidates = []
    signed_url = resolve_cv_view_url(cv_url)
    if signed_url:
        candidates.append(signed_url)
    if cv_url not in candidates:
        candidates.append(cv_url)

    last_error = None
    for fetch_url in candidates:
        try:
            response = requests.get(fetch_url, timeout=30)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', 'application/pdf')
            if 'text/html' in content_type.lower():
                raise ValueError('CV file could not be loaded from storage.')
            return response.content, content_type
        except Exception as error:
            last_error = error
            logger.warning('Failed to fetch CV from %s: %s', fetch_url, error)

    raise last_error or ValueError('CV file could not be loaded.')
