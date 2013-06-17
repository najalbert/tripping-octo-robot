import os
from create_jobs import UploadTracker, _all_pdfs_converted
import subprocess


OUTPUT_FILE = 'skip-list.out'

def main():
    working_dir = os.getcwd()
    for file_name in os.listdir(working_dir):
        full_path = os.path.join(working_dir, file_name)
        if not os.path.isdir(full_path):
            continue
        full_images_path = os.path.join(full_path, 'images')
        if not os.path.isdir(full_images_path):
            print 'Skipping %s.  No images directory.' % full_path
            continue
        if not _all_pdfs_converted(full_images_path):
            print 'Folder %s has not finished PDF conversion, skipping!' % full_path
            continue
        upload_tracker = UploadTracker(full_images_path, quick_init=True)
        if os.path.isfile(upload_tracker.upload_tracker_file):
            pass
            #print 'Folder %s is being uploaded. skipping!' %  full_images_path
            #continue
        sanity_check_jobs(upload_tracker)
        raw_input('continue? ')


def sanity_check_jobs(upload_tracker):
    upload_tracker._get_total_pdf_page_count() # ensures all PDFs have even number of pages
    output_file_name = OUTPUT_FILE + '-' + os.path.basename(os.path.split(upload_tracker.full_path)[0])
    output_file_path = os.path.join(upload_tracker.full_path, output_file_name)
    print 'Outputting skip list to: %s' % output_file_path
    if os.path.isfile(output_file_path):
        print 'Skipping manual portion, %s exists' % output_file_name
        return
    fout = open(output_file_path, 'w')
    for pdf_image_dir_name in os.listdir(upload_tracker.full_path):
        pdf_image_dir = os.path.join(upload_tracker.full_path, pdf_image_dir_name)
        assert os.path.isdir(pdf_image_dir)
        sanity_check_image_dir(upload_tracker, pdf_image_dir, fout)
    fout.close()

def sanity_check_image_dir(upload_tracker, pdf_image_dir, fout):
    even_dir = os.path.join(pdf_image_dir, 'even-pages')
    odd_dir = os.path.join(pdf_image_dir, 'odd-pages')
    assert os.path.isdir(even_dir), 'Not a directory: %s' % even_dir
    assert os.path.isdir(odd_dir), 'Not a directory: %s' % odd_dir
    even_files = [os.path.join(even_dir, f) for f in os.listdir(even_dir)]
    odd_files = [os.path.join(odd_dir, f) for f in os.listdir(odd_dir)]
    if len(even_files) == 0 or len(odd_files) == 0:
        print "Directory with 0 files: %s" % even_dir
        return
    even_files_and_sizes = [(f, os.path.getsize(f)) for f in even_files]
    odd_files_and_sizes = [(f, os.path.getsize(f)) for f in odd_files]
    even_sizes = [t[1] for t in even_files_and_sizes]
    odd_sizes = [t[1] for t in odd_files_and_sizes]
    avg_even_size = sum(even_sizes)/len(even_files)
    avg_odd_size = sum(odd_sizes)/len(odd_files)
    p1_files_and_sizes = None
    p2_files_and_sizes = None
    if avg_even_size > avg_odd_size:
        p1_files_and_sizes = even_files_and_sizes
        p2_files_and_sizes = odd_files_and_sizes
    elif avg_odd_size > avg_even_size:
        p1_files_and_sizes = odd_files_and_sizes
        p2_files_and_sizes = even_files_and_sizes
    else:
        raise Exception('No size winner: %s' % even_dir)

    suspects = []
    while raw_input('Reviewing small P1s... [c]') != 'c':
        pass
    for path, size in p1_files_and_sizes:
        if size < 1260000:
            subprocess.check_output(['open', '-g', path])
            print 'P1 size: %s, File: %s' % (size,path)
            while True:
                answer = raw_input('Okay p1 [y/n]?')
                if 'y' in answer:
                    suspects.append((path, size))
                    fout.write("            '%s',\n" % path)
                    break
                elif 'n' in answer:
                    print 'BONED: %s' % path
                    break

    while raw_input('Reviewing large P2s... [c]') != 'c':
        pass
    for path, size in p2_files_and_sizes:
        if size > 740000:
            subprocess.check_output(['open', '-g', path])
            print 'P2 size: %s, File: %s' % (size,path)
            while True:
                answer = raw_input('Okay p2 [y/n]?')
                if 'y' in answer:
                    suspects.append((path, size))
                    fout.write("            '%s',\n" % path)
                    break
                elif 'n' in answer:
                    print 'BONED: %s' % path
                    break
    p1_min = min([t for t in p1_files_and_sizes if t not in suspects], key=lambda x: x[1])
    p2_max = max([t for t in p2_files_and_sizes if t not in suspects], key=lambda x: x[1])

    assert (p1_min[1] - upload_tracker.FILE_SIZE_DIFFERENTIAL) > p2_max[1], 'Problem: p1_min %s is size %s while p2_max %s is size %s' % (p1_min[0], p1_min[1], p2_max[0], p2_max[1])



if __name__ == "__main__":
    main()
