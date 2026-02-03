from urllib.parse import urlparse
import os 

def is_valid_file_url(url: str) -> bool:
    """
    Returns True if URL points to an actual file, not just a base path.
    """
    path = urlparse(url).path
    filename = os.path.basename(path)
    return bool(filename) 
    


print(is_valid_file_url("https://static.virtuagym.com/videos/"))