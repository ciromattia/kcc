import os
import sys
import zipimport

sys.frozen = True
sys.path = sys.path[:4]
sys.path.insert(0, '/usr/lib/kcc')
sys.path.insert(0, '/usr/local/lib/kcc')
sys.path.insert(0, os.path.join(DIR_NAME, '..', 'lib'))

m = __import__("__main__")
importer = zipimport.zipimporter(INITSCRIPT_ZIP_FILE_NAME)
code = importer.get_code(m.__name__)
exec(code, m.__dict__)
