import os
import subprocess
import time

IMAGE_DIR = 'images'


def main():
    if not image_magick_is_installed():
        return
    for file_name in os.listdir(os.getcwd()):
        make_image_directory()
        if file_name.endswith('.pdf'):
            split_pdf(file_name)

def image_magick_is_installed():
    with open('/dev/null') as devnull:
        try:
            subprocess.call(['pdftocairo'], stdout=devnull, stderr=devnull)
        except OSError:
            print 'Need to install ImageMagick.  Check out http://www.imagemagick.org/script/binary-releases.php'
            return False
    return True

def make_image_directory():
    try:
        os.makedirs(IMAGE_DIR)
    except OSError:
        pass
    assert os.path.isdir(IMAGE_DIR)

def split_pdf(file_name):
    print 'Splitting apart %s' % file_name
    start = time.time()
    output_file = os.path.join(IMAGE_DIR, file_name + '-page')
    arg_list = ['pdftocairo', '-png', '-scale-to', '1600', file_name, output_file]
    with open('/dev/null') as devnull:
        subprocess.call(arg_list, stdout=devnull, stderr=devnull)
    print 'Finished splitting %s in %.02f seconds' % (file_name, time.time() - start)




if __name__ == '__main__':
    main()
