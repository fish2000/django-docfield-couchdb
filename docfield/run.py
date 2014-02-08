
from docfield import settings as docfield_settings
from django.conf import settings
if not settings.configured:
    settings.configure(**docfield_settings.__dict__)

if __name__ == "__main__":
    from django.core.management import call_command
    call_command('test', 'docfield',
        settings='docfield.settings',
        interactive=False, traceback=True, verbosity=2)
    import shutil, sys
    tempdata = docfield_settings.tempdata
    print "Deleting test data: %s" % tempdata
    shutil.rmtree(tempdata)
    sys.exit(0)