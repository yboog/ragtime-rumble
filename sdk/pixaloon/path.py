

def relative_normpath(path, document):
    normroot = document.gameroot.replace('\\', '/').lower()
    if path.replace('\\', '/').lower().startswith(normroot):
        return path.replace('\\', '/')[len(normroot):].strip('/')
    return path.replace('\\', '/').strip('/')