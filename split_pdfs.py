import os
import subprocess
import time
import shutil

IMAGE_EVENS = os.path.join('images', 'even-pages')
IMAGE_ODDS = os.path.join('images', 'odd-pages')

def main():
    if not pdftocairo_is_installed():
        return
    working_dir = os.getcwd()
    for file_name in os.listdir(working_dir):
        full_path = os.path.join(working_dir, file_name)
        if os.path.isdir(full_path):
            split_pdfs_in_directory(full_path)


def split_pdfs_in_directory(full_path):
    file_names = os.listdir(full_path)
    pdf_files = [ file_name for file_name in file_names
                  if file_name.endswith('.pdf') ]
    if len(pdf_files) == 0:
        print 'Skipping %s; no PDFs found.' % full_path
        return
    print 'Converting directory %s.' % full_path
    even_dir, odd_dir = make_image_directories(full_path)
    for file_name in pdf_files:
        full_file_path = os.path.join(full_path, file_name)
        split_pdf(full_file_path, even_dir, odd_dir)

def pdftocairo_is_installed():
    with open('/dev/null') as devnull:
        try:
            subprocess.call(['pdftocairo'], stdout=devnull, stderr=devnull)
        except OSError:
            print 'Need to install pdf2cairo.  Check out the Poppler toolset: http://poppler.freedesktop.org/'
            return False
    return True

def make_image_directories(full_path):
    even_dir = os.path.join(full_path, IMAGE_EVENS)
    odd_dir = os.path.join(full_path, IMAGE_ODDS)
    for directory in [even_dir, odd_dir]:
        try:
            os.makedirs(directory)
        except OSError:
            pass
        assert os.path.isdir(directory)
    return even_dir, odd_dir

def split_pdf(file_path, even_dir, odd_dir):
    print '\tSplitting apart %s' % file_path
    start = time.time()
    size_mb = os.path.getsize(file_path) / 2**20
    output_file = os.path.join(even_dir, os.path.basename(file_path) + '-page')
    arg_list = ['pdftocairo', '-png', '-scale-to', '1600', file_path, output_file]
    with open('/dev/null') as devnull:
        subprocess.call(arg_list, stdout=devnull, stderr=devnull)
    sort_files(file_path, even_dir, odd_dir)
    total_time = time.time() - start
    if total_time > 0:
        print '\tFinished splitting %s in %.02f seconds (%0.02f MB/sec)' % (file_path, total_time, size_mb/total_time)

def sort_files(file_path, even_dir, odd_dir):
    split_files = sorted(os.listdir(even_dir))
    for i, file_name in enumerate(split_files, 1):
        if i % 2 == 1:
            src = os.path.join(even_dir, file_name)
            dst = os.path.join(odd_dir, file_name)
            shutil.move(src, dst)

if __name__ == '__main__':
    main()
