import mimetypes
import uuid
from flask import current_app


def upload_product_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    from .helpers import allowed_file
    if not allowed_file(file_storage.filename):
        raise ValueError('Unsupported image type. Use JPG, JPEG, PNG, or WEBP.')
    if not current_app.config['SUPABASE_URL']:
        raise RuntimeError('Supabase Storage is not configured. Add SUPABASE_URL and a server-side SUPABASE_SERVICE_ROLE_KEY.')
    key = current_app.config['SUPABASE_SERVICE_ROLE_KEY'] or current_app.config['SUPABASE_KEY']
    if not key:
        raise RuntimeError('Supabase storage key is not configured.')
    try:
        from supabase import create_client
        client = create_client(current_app.config['SUPABASE_URL'], key)
        ext = file_storage.filename.rsplit('.', 1)[1].lower()
        path = f'products/{uuid.uuid4().hex}.{ext}'
        content = file_storage.read()
        content_type = file_storage.mimetype or mimetypes.guess_type(file_storage.filename)[0] or 'application/octet-stream'
        client.storage.from_(current_app.config['SUPABASE_BUCKET']).upload(
            path, content, {'content-type': content_type, 'upsert': 'false'}
        )
        return client.storage.from_(current_app.config['SUPABASE_BUCKET']).get_public_url(path)
    except Exception as exc:
        raise RuntimeError(f'Image upload failed: {exc}') from exc
