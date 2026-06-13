import cloudinary.uploader


def upload_teacher_cv(cv_file):
    return cloudinary.uploader.upload(
        cv_file,
        resource_type='raw',
        folder='teacher_cvs',
        type='upload',
        access_mode='public',
    )
