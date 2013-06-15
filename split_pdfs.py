import os
import subprocess
import time
import shutil
import multiprocessing
import Queue

WORKER_COUNT = 4

def main():
    if not pdftocairo_is_installed():
        return
    print "Initializing Work Queue"
    work_queue = multiprocessing.Queue()
    working_dir = os.getcwd()
    for file_name in os.listdir(working_dir):
        full_path = os.path.join(working_dir, file_name)
        if os.path.isdir(full_path):
            add_pdfs_to_work_queue(full_path, work_queue)
    print "Initializing Workers"
    print_lock = multiprocessing.Lock()
    procs = [ multiprocessing.Process(target=worker_main, args=(i, print_lock, work_queue))
              for i in range(WORKER_COUNT) ]
    print "Starting Workers"
    [proc.start() for proc in procs]
    [proc.join() for proc in procs]
    print "All Workers finished"

class WorkerLogger(object):
    def __init__(self, worker_id, print_lock):
        self.worker_id = worker_id
        self.print_lock = print_lock

    def log(self, msg):
        self.print_lock.acquire()
        print 'Worker %s: %s' % (self.worker_id, msg)
        self.print_lock.release()

def worker_main(worker_id, print_lock, work_queue):
    logger = WorkerLogger(worker_id, print_lock)
    logger.log("Worker alive")
    while True:
        try:
            full_path = work_queue.get(timeout=2)
        except Queue.Empty:
            logger.log("Empty queue: worker exiting")
            return
        logger.log("Working on %s" % full_path)
        worker_split_pdf(logger, full_path)

def add_pdfs_to_work_queue(full_path, work_queue):
    file_names = os.listdir(full_path)
    pdf_files = [ os.path.join(full_path, file_name) for file_name in file_names
                  if file_name.endswith('.pdf') ]
    if len(pdf_files) == 0:
        print 'Skipping %s; no PDFs found.' % full_path
        return
    for file_name in pdf_files:
        print 'Adding %s to the work queue.' % file_name
        work_queue.put(file_name)

def worker_split_pdf(logger, full_path):
    even_dir, odd_dir = make_image_directories(full_path)
    _split_pdf(logger, full_path, even_dir, odd_dir)

def pdftocairo_is_installed():
    with open('/dev/null') as devnull:
        try:
            subprocess.call(['pdftocairo'], stdout=devnull, stderr=devnull)
        except OSError:
            print 'Need to install pdf2cairo.  Check out the Poppler toolset: http://poppler.freedesktop.org/'
            return False
    return True

def make_image_directories(full_path):
    path, file_name = os.path.split(full_path)
    even_dir = os.path.join(path, 'images', file_name, 'even-pages')
    odd_dir = os.path.join(path, 'images', file_name, 'odd-pages')
    for directory in [even_dir, odd_dir]:
        try:
            os.makedirs(directory)
        except OSError:
            pass
        assert os.path.isdir(directory)
    return even_dir, odd_dir

def _split_pdf(logger, file_path, even_dir, odd_dir):
    logger.log('\tSplitting apart %s' % file_path)
    start = time.time()
    size_mb = os.path.getsize(file_path) / 2**20
    output_file = os.path.join(even_dir, os.path.basename(file_path) + '-page')
    arg_list = ['pdftocairo', '-png', '-scale-to', '1600', file_path, output_file]
    with open('/dev/null') as devnull:
        subprocess.call(arg_list, stdout=devnull, stderr=devnull)
    sort_files(file_path, even_dir, odd_dir)
    total_time = time.time() - start
    if total_time > 0:
        logger.log('\tFinished splitting %s in %.02f seconds (%0.02f MB/sec)' % (file_path, total_time, size_mb/total_time))

def sort_files(file_path, even_dir, odd_dir):
    split_files = sorted(os.listdir(even_dir))
    for i, file_name in enumerate(split_files, 1):
        if i % 2 == 1:
            src = os.path.join(even_dir, file_name)
            dst = os.path.join(odd_dir, file_name)
            shutil.move(src, dst)

if __name__ == '__main__':
    main()
