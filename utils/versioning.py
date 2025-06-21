import subprocess
import shutil



def get_version_str():
    """
    Return the software's version string using the Git API or
    None if Git is not present in the system.
    """

    short_hash = None
    tag = None

    if shutil.which('git'):
        try:
            short_hash = subprocess.check_output(
                ['git', 'rev-parse', '--short', 'HEAD'],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            tag = subprocess.check_output(
                ['git', 'describe', '--tags', '--exact-match'],
                stderr=subprocess.DEVNULL
            ).decode().strip()

        except subprocess.CalledProcessError:
            pass

    parts = []
    if tag:
        parts.append(f'v{tag}')
    if short_hash:
        parts.append(f'({short_hash})')

    if parts:
        return ' '.join(parts)
    
    return None