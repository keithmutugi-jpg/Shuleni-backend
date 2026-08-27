from django.contrib.auth.hashers import PBKDF2PasswordHasher


class PresentationPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    """Use a faster, still salted PBKDF2 cost for local demonstrations."""

    algorithm = 'pbkdf2_sha256_presentation'
    iterations = 100_000