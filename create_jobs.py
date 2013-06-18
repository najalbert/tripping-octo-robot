'''
This job creation script operates with Mitt Romney-like efficiency to
upload the first page of each converted IPA document to Captricity.
'''
import os
import pickle
import subprocess

# You'll need to install the Captricity API client
# https://github.com/Captricity/captools
from captools.api import Client

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
        upload_images_to_job(full_images_path)

def upload_images_to_job(full_path):
    if not _all_pdfs_converted(full_path):
        print 'Folder %s has not finished PDF conversion, skipping!' % full_path
        return
    upload_tracker = UploadTracker(full_path)
    if upload_tracker.all_uploads_done:
        return
    upload_tracker.create_captricity_job()
    upload_tracker.print_job_info()
    upload_tracker.continue_uploads()
    upload_tracker.print_finished_upload_info()

def _all_pdfs_converted(full_path):
    for pdf_file_name in os.listdir(full_path):
        if not os.path.isdir(os.path.join(full_path, pdf_file_name)):
            continue
        conversion_sigil = os.path.join(full_path, pdf_file_name, 'conversion-done')
        if not os.path.isfile(conversion_sigil):
            return False
    return True

class UploadTracker(object):
    UPLOAD_TRACKER_NAME = 'captricity-upload-status'
    JOB_ID_KEY = 'job_id'
    UPLOADED_INSTANCES_KEY = 'uploaded_instances'
    DOCUMENT_ID = '10145'
    UPLOADS_DONE_NAME = 'captricity-upload-done'
    FILE_SIZE_DIFFERENTIAL = 400000
    # For messed up scans, specify the page count for sanity checks
    MODIFIED_PDF_PAGE_COUNTS = {
            # Baringo
            '/Users/nickj/IPA-data/Baringo/158_Baringo North_A.pdf': 152, # Starts with an extra page 2
            '/Users/nickj/IPA-data/Baringo/161_Mogotio_A.pdf': 64, # Starts with an extra p2, 27 and 28 are p2s
            # Bungoma
            '/Users/nickj/IPA-data/Bungoma/222_Webuye West.pdf': 0, # PDF file is corrupt
            '/Users/nickj/IPA-data/Kitui/070_Kitui West_A.pdf': 156, # 2x page count, only p1s were scanned
            '/Users/nickj/IPA-data/Kitui/070_Kitui West_B.pdf': 102, # 2x page count, only p1s were scanned
            '/Users/nickj/IPA-data/Kitui/072_Kitui Central_A.pdf': 46, # 2x page count, only p1s were scanned
            '/Users/nickj/IPA-data/Kitui/072_Kitui Central_B.pdf': 110, # 2x page count, only p1s were scanned
            '/Users/nickj/IPA-data/Kitui/072_Kitui Central_C.pdf': 70, # 2x page count, only p1s were scanned
            '/Users/nickj/IPA-data/Laikipia/163_Laikipia West_A.pdf': 160, # double scanned p2

            '/Users/nickj/IPA-data/Vihiga/212_Sabatia.pdf': 0, # PDF file is corrupt
    }

    # Lists of files to ignore when doing file size sanity checks.
    # These are mostly the "bad" page 1s
    FILE_SIZE_SKIP_LIST = [
            # Baringo (different version p1s)
            '/Users/nickj/IPA-data/Baringo/images/160_Baringo South_A.pdf/odd-pages/160_Baringo South_A.pdf-page-133.png',
            '/Users/nickj/IPA-data/Baringo/images/160_Baringo South_A.pdf/odd-pages/160_Baringo South_A.pdf-page-093.png',
            '/Users/nickj/IPA-data/Baringo/images/160_Baringo South_A.pdf/odd-pages/160_Baringo South_A.pdf-page-017.png',
            '/Users/nickj/IPA-data/Baringo/images/160_Baringo South_B.pdf/odd-pages/160_Baringo South_B.pdf-page-119.png',
            '/Users/nickj/IPA-data/Baringo/images/160_Baringo South_B.pdf/odd-pages/160_Baringo South_B.pdf-page-057.png',
            '/Users/nickj/IPA-data/Baringo/images/160_Baringo South_B.pdf/odd-pages/160_Baringo South_B.pdf-page-059.png',
            '/Users/nickj/IPA-data/Baringo/images/160_Baringo South_B.pdf/odd-pages/160_Baringo South_B.pdf-page-003.png',
            # Bomet (really big p2)
            '/Users/nickj/IPA-data/Bomet/images/196_Bomet East.pdf/even-pages/196_Bomet East.pdf-page-072.png',
            '/Users/nickj/IPA-data/Bomet/images/198_Konoin.pdf/even-pages/198_Konoin.pdf-page-058.png',
            # Bungoma
            '/Users/nickj/IPA-data/Bungoma/images/220_Kanduyi_B.pdf/odd-pages/220_Kanduyi_B.pdf-page-21.png', # p1 version
            '/Users/nickj/IPA-data/Bungoma/images/220_Kanduyi_B.pdf/even-pages/220_Kanduyi_B.pdf-page-22.png', # big p2
            '/Users/nickj/IPA-data/Bungoma/images/220_Kanduyi_C.pdf/odd-pages/220_Kanduyi_C.pdf-page-47.png', # p1 version
            # Busia
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-009.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-011.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-013.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-017.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-019.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-053.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-055.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-075.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-077.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-079.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-081.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-083.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-085.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-095.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-097.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-119.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-121.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-139.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-141.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-143.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-145.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-149.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-151.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-153.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-159.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-161.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-163.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-165.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-167.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-169.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-171.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-173.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/odd-pages/228_Matayos.pdf-page-175.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/even-pages/228_Matayos.pdf-page-144.png',
            '/Users/nickj/IPA-data/Busia/images/228_Matayos.pdf/even-pages/228_Matayos.pdf-page-146.png',
            '/Users/nickj/IPA-data/Busia/images/230_Funyula_A.pdf/odd-pages/230_Funyula_A.pdf-page-01.png',
            '/Users/nickj/IPA-data/Busia/images/230_Funyula_A.pdf/odd-pages/230_Funyula_A.pdf-page-11.png',
            '/Users/nickj/IPA-data/Busia/images/230_Funyula_C.pdf/odd-pages/230_Funyula_C.pdf-page-01.png',
            '/Users/nickj/IPA-data/Busia/images/230_Funyula_C.pdf/odd-pages/230_Funyula_C.pdf-page-03.png',
            '/Users/nickj/IPA-data/Busia/images/230_Funyula_C.pdf/odd-pages/230_Funyula_C.pdf-page-57.png',

            #Embu
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-004.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-028.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-032.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-036.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-038.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-040.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-042.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-050.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-052.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-054.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-060.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-062.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-064.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-066.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-070.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-072.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-074.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-082.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-084.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-086.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-090.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-092.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-094.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-098.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-100.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-104.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-112.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_A.pdf/even-pages/063_Manyatta_A.pdf-page-116.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/odd-pages/063_Manyatta_B.pdf-page-143.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-002.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-012.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-014.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-016.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-020.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-022.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-024.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-026.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-028.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-032.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-034.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-040.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-042.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-044.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-046.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-050.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-052.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-054.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-056.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-062.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-064.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-066.png',
            '/Users/nickj/IPA-data/Embu/images/063_Manyatta_B.pdf/even-pages/063_Manyatta_B.pdf-page-068.png',
            '/Users/nickj/IPA-data/Embu/images/064_Runyenjes_A.pdf/odd-pages/064_Runyenjes_A.pdf-page-031.png',
            '/Users/nickj/IPA-data/Embu/images/064_Runyenjes_A.pdf/odd-pages/064_Runyenjes_A.pdf-page-057.png',
            '/Users/nickj/IPA-data/Embu/images/064_Runyenjes_A.pdf/odd-pages/064_Runyenjes_A.pdf-page-171.png',
            '/Users/nickj/IPA-data/Embu/images/064_Runyenjes_A.pdf/even-pages/064_Runyenjes_A.pdf-page-104.png',
            '/Users/nickj/IPA-data/Embu/images/064_Runyenjes_B.pdf/odd-pages/064_Runyenjes_B.pdf-page-057.png',
            '/Users/nickj/IPA-data/Embu/images/064_Runyenjes_B.pdf/odd-pages/064_Runyenjes_B.pdf-page-065.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/odd-pages/065_Mbeere South.pdf-page-105.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/odd-pages/065_Mbeere South.pdf-page-125.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/odd-pages/065_Mbeere South.pdf-page-167.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/odd-pages/065_Mbeere South.pdf-page-173.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/odd-pages/065_Mbeere South.pdf-page-179.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/odd-pages/065_Mbeere South.pdf-page-187.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/odd-pages/065_Mbeere South.pdf-page-199.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/odd-pages/065_Mbeere South.pdf-page-201.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/odd-pages/065_Mbeere South.pdf-page-223.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/odd-pages/065_Mbeere South.pdf-page-233.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/odd-pages/065_Mbeere South.pdf-page-251.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/odd-pages/065_Mbeere South.pdf-page-261.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/odd-pages/065_Mbeere South.pdf-page-273.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/odd-pages/065_Mbeere South.pdf-page-279.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/odd-pages/065_Mbeere South.pdf-page-281.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-012.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-028.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-040.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-042.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-048.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-056.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-058.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-060.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-062.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-076.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-078.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-082.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-084.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-086.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-088.png',
            '/Users/nickj/IPA-data/Embu/images/065_Mbeere South.pdf/even-pages/065_Mbeere South.pdf-page-092.png',
            '/Users/nickj/IPA-data/Embu/images/066_Mbeere North.pdf/odd-pages/066_Mbeere North.pdf-page-023.png',
            '/Users/nickj/IPA-data/Embu/images/066_Mbeere North.pdf/odd-pages/066_Mbeere North.pdf-page-051.png',
            '/Users/nickj/IPA-data/Embu/images/066_Mbeere North.pdf/odd-pages/066_Mbeere North.pdf-page-163.png',

            # Garissa
            '/Users/nickj/IPA-data/Garissa/images/027_Garissa Township.pdf/odd-pages/027_Garissa Township.pdf-page-097.png',
            '/Users/nickj/IPA-data/Garissa/images/028_Balambala.pdf/odd-pages/028_Balambala.pdf-page-85.png',
            '/Users/nickj/IPA-data/Garissa/images/028_Balambala.pdf/odd-pages/028_Balambala.pdf-page-91.png',
            '/Users/nickj/IPA-data/Garissa/images/031_Fafi_A.pdf/odd-pages/031_Fafi_A.pdf-page-59.png',
            '/Users/nickj/IPA-data/Garissa/images/031_Fafi_B.pdf/odd-pages/031_Fafi_B.pdf-page-01.png',
            '/Users/nickj/IPA-data/Garissa/images/031_Fafi_B.pdf/odd-pages/031_Fafi_B.pdf-page-15.png',
            '/Users/nickj/IPA-data/Garissa/images/031_Fafi_B.pdf/odd-pages/031_Fafi_B.pdf-page-31.png',
            '/Users/nickj/IPA-data/Garissa/images/031_Fafi_B.pdf/odd-pages/031_Fafi_B.pdf-page-33.png',
            '/Users/nickj/IPA-data/Garissa/images/031_Fafi_B.pdf/odd-pages/031_Fafi_B.pdf-page-45.png',
            '/Users/nickj/IPA-data/Garissa/images/032_Ijara.pdf/even-pages/032_Ijara.pdf-page-108.png',

            # Homabay
            '/Users/nickj/IPA-data/Homabay/images/245_Kasipul.pdf/even-pages/245_Kasipul.pdf-page-012.png',
            '/Users/nickj/IPA-data/Homabay/images/246_Kabondo Kasipul_A.pdf/odd-pages/246_Kabondo Kasipul_A.pdf-page-41.png',
            '/Users/nickj/IPA-data/Homabay/images/246_Kabondo Kasipul_A.pdf/odd-pages/246_Kabondo Kasipul_A.pdf-page-53.png',
            '/Users/nickj/IPA-data/Homabay/images/246_Kabondo Kasipul_A.pdf/odd-pages/246_Kabondo Kasipul_A.pdf-page-87.png',
            '/Users/nickj/IPA-data/Homabay/images/246_Kabondo Kasipul_B.pdf/odd-pages/246_Kabondo Kasipul_B.pdf-page-37.png',
            '/Users/nickj/IPA-data/Homabay/images/246_Kabondo Kasipul_B.pdf/odd-pages/246_Kabondo Kasipul_B.pdf-page-39.png',
            '/Users/nickj/IPA-data/Homabay/images/246_Kabondo Kasipul_B.pdf/odd-pages/246_Kabondo Kasipul_B.pdf-page-47.png',

            # Isiolo
            '/Users/nickj/IPA-data/Isiolo/images/049_Isiolo North_A.pdf/odd-pages/049_Isiolo North_A.pdf-page-019.png',
            '/Users/nickj/IPA-data/Isiolo/images/049_Isiolo North_A.pdf/odd-pages/049_Isiolo North_A.pdf-page-021.png',
            '/Users/nickj/IPA-data/Isiolo/images/049_Isiolo North_A.pdf/even-pages/049_Isiolo North_A.pdf-page-006.png',
            '/Users/nickj/IPA-data/Isiolo/images/049_Isiolo North_A.pdf/even-pages/049_Isiolo North_A.pdf-page-024.png',
            '/Users/nickj/IPA-data/Isiolo/images/049_Isiolo North_A.pdf/even-pages/049_Isiolo North_A.pdf-page-030.png',
            '/Users/nickj/IPA-data/Isiolo/images/049_Isiolo North_A.pdf/even-pages/049_Isiolo North_A.pdf-page-032.png',
            '/Users/nickj/IPA-data/Isiolo/images/049_Isiolo North_A.pdf/even-pages/049_Isiolo North_A.pdf-page-040.png',
            '/Users/nickj/IPA-data/Isiolo/images/049_Isiolo North_A.pdf/even-pages/049_Isiolo North_A.pdf-page-046.png',
            '/Users/nickj/IPA-data/Isiolo/images/049_Isiolo North_A.pdf/even-pages/049_Isiolo North_A.pdf-page-048.png',
            '/Users/nickj/IPA-data/Isiolo/images/049_Isiolo North_A.pdf/even-pages/049_Isiolo North_A.pdf-page-050.png',
            '/Users/nickj/IPA-data/Isiolo/images/049_Isiolo North_A.pdf/even-pages/049_Isiolo North_A.pdf-page-052.png',
            '/Users/nickj/IPA-data/Isiolo/images/049_Isiolo North_A.pdf/even-pages/049_Isiolo North_A.pdf-page-058.png',
            '/Users/nickj/IPA-data/Isiolo/images/049_Isiolo North_A.pdf/even-pages/049_Isiolo North_A.pdf-page-066.png',
            '/Users/nickj/IPA-data/Isiolo/images/049_Isiolo North_A.pdf/even-pages/049_Isiolo North_A.pdf-page-074.png',

            # Kajiado
            '/Users/nickj/IPA-data/Kajiado/images/183_Kajiado North_A.pdf/odd-pages/183_Kajiado North_A.pdf-page-47.png',
            '/Users/nickj/IPA-data/Kajiado/images/183_Kajiado North_A.pdf/odd-pages/183_Kajiado North_A.pdf-page-63.png',
            '/Users/nickj/IPA-data/Kajiado/images/183_Kajiado North_A.pdf/even-pages/183_Kajiado North_A.pdf-page-68.png',
            '/Users/nickj/IPA-data/Kajiado/images/183_Kajiado North_B.pdf/odd-pages/183_Kajiado North_B.pdf-page-39.png',
            '/Users/nickj/IPA-data/Kajiado/images/183_Kajiado North_B.pdf/even-pages/183_Kajiado North_B.pdf-page-86.png',
            '/Users/nickj/IPA-data/Kajiado/images/183_Kajiado North_D.pdf/even-pages/183_Kajiado North_D.pdf-page-14.png',

            # Kakamega
            '/Users/nickj/IPA-data/Kakamega/images/199_Lugari.pdf/odd-pages/199_Lugari.pdf-page-103.png',
            '/Users/nickj/IPA-data/Kakamega/images/200_Likuyani.pdf/odd-pages/200_Likuyani.pdf-page-085.png',
            '/Users/nickj/IPA-data/Kakamega/images/200_Likuyani.pdf/odd-pages/200_Likuyani.pdf-page-087.png',
            '/Users/nickj/IPA-data/Kakamega/images/203_Navakholo_A.pdf/odd-pages/203_Navakholo_A.pdf-page-09.png',
            '/Users/nickj/IPA-data/Kakamega/images/203_Navakholo_A.pdf/odd-pages/203_Navakholo_A.pdf-page-11.png',
            '/Users/nickj/IPA-data/Kakamega/images/203_Navakholo_A.pdf/odd-pages/203_Navakholo_A.pdf-page-19.png',
            '/Users/nickj/IPA-data/Kakamega/images/203_Navakholo_A.pdf/odd-pages/203_Navakholo_A.pdf-page-21.png',
            '/Users/nickj/IPA-data/Kakamega/images/203_Navakholo_B.pdf/odd-pages/203_Navakholo_B.pdf-page-021.png',
            '/Users/nickj/IPA-data/Kakamega/images/203_Navakholo_B.pdf/odd-pages/203_Navakholo_B.pdf-page-027.png',
            '/Users/nickj/IPA-data/Kakamega/images/203_Navakholo_B.pdf/odd-pages/203_Navakholo_B.pdf-page-081.png',
            '/Users/nickj/IPA-data/Kakamega/images/203_Navakholo_B.pdf/odd-pages/203_Navakholo_B.pdf-page-089.png',
            '/Users/nickj/IPA-data/Kakamega/images/203_Navakholo_B.pdf/odd-pages/203_Navakholo_B.pdf-page-123.png',
            '/Users/nickj/IPA-data/Kakamega/images/203_Navakholo_B.pdf/odd-pages/203_Navakholo_B.pdf-page-129.png',
            '/Users/nickj/IPA-data/Kakamega/images/203_Navakholo_B.pdf/odd-pages/203_Navakholo_B.pdf-page-133.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_A.pdf/odd-pages/205_Mumias East_A.pdf-page-01.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_A.pdf/odd-pages/205_Mumias East_A.pdf-page-03.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_A.pdf/odd-pages/205_Mumias East_A.pdf-page-05.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_A.pdf/odd-pages/205_Mumias East_A.pdf-page-07.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_A.pdf/odd-pages/205_Mumias East_A.pdf-page-31.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_A.pdf/odd-pages/205_Mumias East_A.pdf-page-33.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_A.pdf/odd-pages/205_Mumias East_A.pdf-page-35.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_A.pdf/odd-pages/205_Mumias East_A.pdf-page-37.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_A.pdf/odd-pages/205_Mumias East_A.pdf-page-45.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_A.pdf/odd-pages/205_Mumias East_A.pdf-page-47.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_A.pdf/odd-pages/205_Mumias East_A.pdf-page-49.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_A.pdf/odd-pages/205_Mumias East_A.pdf-page-51.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_A.pdf/odd-pages/205_Mumias East_A.pdf-page-55.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-003.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-005.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-007.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-009.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-045.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-047.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-049.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-051.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-057.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-059.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-061.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-063.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-067.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-069.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-071.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-073.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-075.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-077.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-079.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-081.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-085.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-087.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-089.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-091.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-095.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-097.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-099.png',
            '/Users/nickj/IPA-data/Kakamega/images/205_Mumias East_B.pdf/odd-pages/205_Mumias East_B.pdf-page-101.png',
            '/Users/nickj/IPA-data/Kakamega/images/207_Butere_A.pdf/odd-pages/207_Butere_A.pdf-page-05.png',
            '/Users/nickj/IPA-data/Kakamega/images/207_Butere_A.pdf/odd-pages/207_Butere_A.pdf-page-07.png',
            '/Users/nickj/IPA-data/Kakamega/images/207_Butere_A.pdf/odd-pages/207_Butere_A.pdf-page-29.png',
            '/Users/nickj/IPA-data/Kakamega/images/207_Butere_A.pdf/odd-pages/207_Butere_A.pdf-page-31.png',
            '/Users/nickj/IPA-data/Kakamega/images/207_Butere_B.pdf/odd-pages/207_Butere_B.pdf-page-015.png',
            '/Users/nickj/IPA-data/Kakamega/images/207_Butere_B.pdf/odd-pages/207_Butere_B.pdf-page-017.png',
            '/Users/nickj/IPA-data/Kakamega/images/207_Butere_B.pdf/odd-pages/207_Butere_B.pdf-page-043.png',
            '/Users/nickj/IPA-data/Kakamega/images/207_Butere_B.pdf/odd-pages/207_Butere_B.pdf-page-045.png',
            '/Users/nickj/IPA-data/Kakamega/images/207_Butere_B.pdf/odd-pages/207_Butere_B.pdf-page-109.png',
            '/Users/nickj/IPA-data/Kakamega/images/209_Shinyalu_B.pdf/odd-pages/209_Shinyalu_B.pdf-page-085.png',
            '/Users/nickj/IPA-data/Kakamega/images/210_Ikolomani.pdf/odd-pages/210_Ikolomani.pdf-page-035.png',

            # Kericho
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-003.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-017.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-025.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-031.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-041.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-049.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-051.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-063.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-065.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-069.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-109.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-111.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-119.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-153.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-167.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-169.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-177.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-183.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-185.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-215.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-233.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-239.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-257.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-267.png',
            '/Users/nickj/IPA-data/Kericho/images/190_Ainamoi.pdf/odd-pages/190_Ainamoi.pdf-page-277.png',
            '/Users/nickj/IPA-data/Kericho/images/192_Belgut.pdf/odd-pages/192_Belgut.pdf-page-033.png',

            # Kilifi
            '/Users/nickj/IPA-data/Kilifi/images/012_Kilifi South_A.pdf/odd-pages/012_Kilifi South_A.pdf-page-23.png',
            '/Users/nickj/IPA-data/Kilifi/images/012_Kilifi South_D.pdf/odd-pages/012_Kilifi South_D.pdf-page-19.png',
            '/Users/nickj/IPA-data/Kilifi/images/012_Kilifi South_D.pdf/odd-pages/012_Kilifi South_D.pdf-page-21.png',
            '/Users/nickj/IPA-data/Kilifi/images/012_Kilifi South_D.pdf/odd-pages/012_Kilifi South_D.pdf-page-23.png',
            '/Users/nickj/IPA-data/Kilifi/images/012_Kilifi South_D.pdf/odd-pages/012_Kilifi South_D.pdf-page-25.png',
            '/Users/nickj/IPA-data/Kilifi/images/012_Kilifi South_D.pdf/odd-pages/012_Kilifi South_D.pdf-page-53.png',
            '/Users/nickj/IPA-data/Kilifi/images/012_Kilifi South_E.pdf/odd-pages/012_Kilifi South_E.pdf-page-23.png',
            '/Users/nickj/IPA-data/Kilifi/images/012_Kilifi South_E.pdf/odd-pages/012_Kilifi South_E.pdf-page-33.png',
            '/Users/nickj/IPA-data/Kilifi/images/012_Kilifi South_E.pdf/odd-pages/012_Kilifi South_E.pdf-page-35.png',
            '/Users/nickj/IPA-data/Kilifi/images/012_Kilifi South_E.pdf/odd-pages/012_Kilifi South_E.pdf-page-45.png',
            '/Users/nickj/IPA-data/Kilifi/images/012_Kilifi South_E.pdf/odd-pages/012_Kilifi South_E.pdf-page-47.png',
            '/Users/nickj/IPA-data/Kilifi/images/012_Kilifi South_E.pdf/even-pages/012_Kilifi South_E.pdf-page-34.png',
            '/Users/nickj/IPA-data/Kilifi/images/013_Kaloleni.pdf/even-pages/013_Kaloleni.pdf-page-018.png',
            '/Users/nickj/IPA-data/Kilifi/images/013_Kaloleni.pdf/even-pages/013_Kaloleni.pdf-page-036.png',
            '/Users/nickj/IPA-data/Kilifi/images/014_Rabai.pdf/odd-pages/014_Rabai.pdf-page-101.png',
            '/Users/nickj/IPA-data/Kilifi/images/015_Ganze_A.pdf/odd-pages/015_Ganze_A.pdf-page-007.png',
            '/Users/nickj/IPA-data/Kilifi/images/015_Ganze_A.pdf/odd-pages/015_Ganze_A.pdf-page-067.png',
            '/Users/nickj/IPA-data/Kilifi/images/016_Malindi.pdf/even-pages/016_Malindi.pdf-page-082.png',
            '/Users/nickj/IPA-data/Kilifi/images/017_Magarini.pdf/even-pages/017_Magarini.pdf-page-010.png',

            # Kirinyaga
            '/Users/nickj/IPA-data/Kirinyaga/images/101_Gichugu_B.pdf/even-pages/101_Gichugu_B.pdf-page-054.png',
            '/Users/nickj/IPA-data/Kirinyaga/images/103_Kirinyaga Central.pdf/odd-pages/103_Kirinyaga Central.pdf-page-115.png',
            '/Users/nickj/IPA-data/Kirinyaga/images/103_Kirinyaga Central.pdf/odd-pages/103_Kirinyaga Central.pdf-page-003.png',
            '/Users/nickj/IPA-data/Kirinyaga/images/103_Kirinyaga Central.pdf/odd-pages/103_Kirinyaga Central.pdf-page-007.png',
            '/Users/nickj/IPA-data/Kirinyaga/images/103_Kirinyaga Central.pdf/odd-pages/103_Kirinyaga Central.pdf-page-169.png',
            '/Users/nickj/IPA-data/Kirinyaga/images/103_Kirinyaga Central.pdf/even-pages/103_Kirinyaga Central.pdf-page-130.png',

            # Kisumu
            '/Users/nickj/IPA-data/Kisumu/images/242_Nyando_B.pdf/odd-pages/242_Nyando_B.pdf-page-31.png',
            '/Users/nickj/IPA-data/Kisumu/images/242_Nyando_B.pdf/odd-pages/242_Nyando_B.pdf-page-15.png',
            '/Users/nickj/IPA-data/Kisumu/images/242_Nyando_B.pdf/odd-pages/242_Nyando_B.pdf-page-05.png',
            '/Users/nickj/IPA-data/Kisumu/images/242_Nyando_B.pdf/odd-pages/242_Nyando_B.pdf-page-49.png',
            '/Users/nickj/IPA-data/Kisumu/images/242_Nyando_C.pdf/odd-pages/242_Nyando_C.pdf-page-73.png',
            '/Users/nickj/IPA-data/Kisumu/images/242_Nyando_C.pdf/odd-pages/242_Nyando_C.pdf-page-43.png',
            '/Users/nickj/IPA-data/Kisumu/images/242_Nyando_C.pdf/odd-pages/242_Nyando_C.pdf-page-81.png',
            '/Users/nickj/IPA-data/Kisumu/images/242_Nyando_C.pdf/odd-pages/242_Nyando_C.pdf-page-63.png',
            '/Users/nickj/IPA-data/Kisumu/images/242_Nyando_C.pdf/odd-pages/242_Nyando_C.pdf-page-55.png',
            '/Users/nickj/IPA-data/Kisumu/images/242_Nyando_C.pdf/odd-pages/242_Nyando_C.pdf-page-49.png',

            # Kwale
            '/Users/nickj/IPA-data/Kwale/images/008_Lunga Lunga_A.pdf/odd-pages/008_Lunga Lunga_A.pdf-page-15.png',

            # Laikipia
            #'/Users/nickj/IPA-data/Laikipia/images/165_Laikipia North_B.pdf/odd-pages/165_Laikipia North_B.pdf-page-1.png',

            # Makueni
            '/Users/nickj/IPA-data/Makueni/images/083_Mbooni_A.pdf/even-pages/083_Mbooni_A.pdf-page-132.png',
            '/Users/nickj/IPA-data/Makueni/images/083_Mbooni_B.pdf/even-pages/083_Mbooni_B.pdf-page-118.png',
            '/Users/nickj/IPA-data/Makueni/images/083_Mbooni_B.pdf/even-pages/083_Mbooni_B.pdf-page-090.png',
            '/Users/nickj/IPA-data/Makueni/images/083_Mbooni_B.pdf/even-pages/083_Mbooni_B.pdf-page-086.png',
            '/Users/nickj/IPA-data/Makueni/images/084_Kilome.pdf/even-pages/084_Kilome.pdf-page-066.png',
            '/Users/nickj/IPA-data/Makueni/images/085_Kaiti_A.pdf/even-pages/085_Kaiti_A.pdf-page-86.png',
            '/Users/nickj/IPA-data/Makueni/images/085_Kaiti_A.pdf/even-pages/085_Kaiti_A.pdf-page-02.png',
            '/Users/nickj/IPA-data/Makueni/images/087_Kibwezi West_B.pdf/even-pages/087_Kibwezi West_B.pdf-page-052.png',
            '/Users/nickj/IPA-data/Makueni/images/087_Kibwezi West_B.pdf/even-pages/087_Kibwezi West_B.pdf-page-036.png',
            '/Users/nickj/IPA-data/Makueni/images/087_Kibwezi West_C.pdf/even-pages/087_Kibwezi West_C.pdf-page-076.png',
            '/Users/nickj/IPA-data/Makueni/images/087_Kibwezi West_C.pdf/even-pages/087_Kibwezi West_C.pdf-page-016.png',
            '/Users/nickj/IPA-data/Makueni/images/088_Kibwezi East_A.pdf/even-pages/088_Kibwezi East_A.pdf-page-74.png',
            '/Users/nickj/IPA-data/Makueni/images/088_Kibwezi East_B.pdf/even-pages/088_Kibwezi East_B.pdf-page-052.png',
            '/Users/nickj/IPA-data/Makueni/images/088_Kibwezi East_C.pdf/even-pages/088_Kibwezi East_C.pdf-page-24.png',

            # Marsabit
            '/Users/nickj/IPA-data/Marsabit/images/045_Moyale_B.pdf/even-pages/045_Moyale_B.pdf-page-080.png',
            '/Users/nickj/IPA-data/Marsabit/images/047_Saku.pdf/odd-pages/047_Saku.pdf-page-109.png',
            '/Users/nickj/IPA-data/Marsabit/images/047_Saku.pdf/even-pages/047_Saku.pdf-page-008.png',
            '/Users/nickj/IPA-data/Marsabit/images/047_Saku.pdf/even-pages/047_Saku.pdf-page-072.png',
            '/Users/nickj/IPA-data/Marsabit/images/048_Laisamis.pdf/even-pages/048_Laisamis.pdf-page-126.png',
            '/Users/nickj/IPA-data/Marsabit/images/048_Laisamis.pdf/even-pages/048_Laisamis.pdf-page-064.png',
            '/Users/nickj/IPA-data/Marsabit/images/048_Laisamis.pdf/even-pages/048_Laisamis.pdf-page-134.png',

            # Meru
            '/Users/nickj/IPA-data/Meru/images/051_Igembe South.pdf/even-pages/051_Igembe South.pdf-page-028.png',
            '/Users/nickj/IPA-data/Meru/images/051_Igembe South.pdf/even-pages/051_Igembe South.pdf-page-022.png',
            '/Users/nickj/IPA-data/Meru/images/052_Igembe Central_A.pdf/odd-pages/052_Igembe Central_A.pdf-page-093.png',
            '/Users/nickj/IPA-data/Meru/images/052_Igembe Central_A.pdf/odd-pages/052_Igembe Central_A.pdf-page-097.png',
            '/Users/nickj/IPA-data/Meru/images/052_Igembe Central_A.pdf/odd-pages/052_Igembe Central_A.pdf-page-091.png',
            '/Users/nickj/IPA-data/Meru/images/052_Igembe Central_A.pdf/odd-pages/052_Igembe Central_A.pdf-page-095.png',
            '/Users/nickj/IPA-data/Meru/images/053_Igembe North_A.pdf/odd-pages/053_Igembe North_A.pdf-page-055.png',
            '/Users/nickj/IPA-data/Meru/images/053_Igembe North_A.pdf/even-pages/053_Igembe North_A.pdf-page-056.png',
            '/Users/nickj/IPA-data/Meru/images/053_Igembe North_B.pdf/even-pages/053_Igembe North_B.pdf-page-060.png',
            '/Users/nickj/IPA-data/Meru/images/055_Tigania East_B.pdf/even-pages/055_Tigania East_B.pdf-page-062.png',
            '/Users/nickj/IPA-data/Meru/images/055_Tigania East_B.pdf/even-pages/055_Tigania East_B.pdf-page-056.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-072.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-076.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-112.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-048.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-104.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-074.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-030.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-050.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-084.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-038.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-086.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-092.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-034.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-068.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-114.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-042.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-096.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-102.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-122.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-082.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-066.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-078.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-106.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-098.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-088.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-052.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-046.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-058.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-116.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-026.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-090.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-064.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-062.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-036.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-100.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-032.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-044.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-070.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-080.png',
            '/Users/nickj/IPA-data/Meru/images/056_North Imenti_A.pdf/even-pages/056_North Imenti_A.pdf-page-020.png',
            '/Users/nickj/IPA-data/Meru/images/057_Buuri_A.pdf/even-pages/057_Buuri_A.pdf-page-008.png',
            '/Users/nickj/IPA-data/Meru/images/057_Buuri_B.pdf/even-pages/057_Buuri_B.pdf-page-82.png',
            '/Users/nickj/IPA-data/Meru/images/057_Buuri_B.pdf/even-pages/057_Buuri_B.pdf-page-20.png',
            '/Users/nickj/IPA-data/Meru/images/058_Central Imenti_A.pdf/odd-pages/058_Central Imenti_A.pdf-page-035.png',
            '/Users/nickj/IPA-data/Meru/images/058_Central Imenti_A.pdf/even-pages/058_Central Imenti_A.pdf-page-036.png',
            '/Users/nickj/IPA-data/Meru/images/058_Central Imenti_B.pdf/even-pages/058_Central Imenti_B.pdf-page-12.png',
            '/Users/nickj/IPA-data/Meru/images/059_South Imenti_C.pdf/even-pages/059_South Imenti_C.pdf-page-028.png',

            # Mombasa
            '/Users/nickj/IPA-data/Mombasa/images/003_Kisauni_A.pdf/odd-pages/003_Kisauni_A.pdf-page-37.png',
            '/Users/nickj/IPA-data/Mombasa/images/003_Kisauni_A.pdf/odd-pages/003_Kisauni_A.pdf-page-35.png',
            '/Users/nickj/IPA-data/Mombasa/images/003_Kisauni_B.pdf/odd-pages/003_Kisauni_B.pdf-page-03.png',
            '/Users/nickj/IPA-data/Mombasa/images/003_Kisauni_C.pdf/odd-pages/003_Kisauni_C.pdf-page-45.png',
            '/Users/nickj/IPA-data/Mombasa/images/003_Kisauni_C.pdf/odd-pages/003_Kisauni_C.pdf-page-21.png',
            '/Users/nickj/IPA-data/Mombasa/images/003_Kisauni_C.pdf/odd-pages/003_Kisauni_C.pdf-page-27.png',
            '/Users/nickj/IPA-data/Mombasa/images/003_Kisauni_C.pdf/odd-pages/003_Kisauni_C.pdf-page-43.png',
            '/Users/nickj/IPA-data/Mombasa/images/003_Kisauni_C.pdf/odd-pages/003_Kisauni_C.pdf-page-23.png',
            '/Users/nickj/IPA-data/Mombasa/images/003_Kisauni_C.pdf/odd-pages/003_Kisauni_C.pdf-page-03.png',
            '/Users/nickj/IPA-data/Mombasa/images/003_Kisauni_E.pdf/odd-pages/003_Kisauni_E.pdf-page-11.png',
            '/Users/nickj/IPA-data/Mombasa/images/003_Kisauni_G.pdf/odd-pages/003_Kisauni_G.pdf-page-53.png',
            '/Users/nickj/IPA-data/Mombasa/images/003_Kisauni_H.pdf/odd-pages/003_Kisauni_H.pdf-page-07.png',
            '/Users/nickj/IPA-data/Mombasa/images/006_Mvita_A.pdf/odd-pages/006_Mvita_A.pdf-page-077.png',
            '/Users/nickj/IPA-data/Mombasa/images/006_Mvita_A.pdf/odd-pages/006_Mvita_A.pdf-page-079.png',
            '/Users/nickj/IPA-data/Mombasa/images/006_Mvita_A.pdf/odd-pages/006_Mvita_A.pdf-page-089.png',
            '/Users/nickj/IPA-data/Mombasa/images/006_Mvita_A.pdf/odd-pages/006_Mvita_A.pdf-page-043.png',
            '/Users/nickj/IPA-data/Mombasa/images/006_Mvita_B.pdf/odd-pages/006_Mvita_B.pdf-page-069.png',
            '/Users/nickj/IPA-data/Mombasa/images/006_Mvita_B.pdf/odd-pages/006_Mvita_B.pdf-page-029.png',
            '/Users/nickj/IPA-data/Mombasa/images/006_Mvita_B.pdf/odd-pages/006_Mvita_B.pdf-page-061.png',
            '/Users/nickj/IPA-data/Mombasa/images/006_Mvita_B.pdf/odd-pages/006_Mvita_B.pdf-page-031.png',
            '/Users/nickj/IPA-data/Mombasa/images/006_Mvita_B.pdf/odd-pages/006_Mvita_B.pdf-page-067.png',

            # Muranga
            '/Users/nickj/IPA-data/Muranga/images/108_Maragwa.pdf/odd-pages/108_Maragwa.pdf-page-229.png',
            '/Users/nickj/IPA-data/Muranga/images/108_Maragwa.pdf/odd-pages/108_Maragwa.pdf-page-239.png',
            '/Users/nickj/IPA-data/Muranga/images/108_Maragwa.pdf/odd-pages/108_Maragwa.pdf-page-205.png',
            '/Users/nickj/IPA-data/Muranga/images/108_Maragwa.pdf/odd-pages/108_Maragwa.pdf-page-129.png',

            # Nairobi
            '/Users/nickj/IPA-data/Nairobi/images/276_Dagoretti South_A.pdf/odd-pages/276_Dagoretti South_A.pdf-page-19.png',
            '/Users/nickj/IPA-data/Nairobi/images/276_Dagoretti South_B.pdf/odd-pages/276_Dagoretti South_B.pdf-page-15.png',
            '/Users/nickj/IPA-data/Nairobi/images/276_Dagoretti South_C.pdf/odd-pages/276_Dagoretti South_C.pdf-page-09.png',

            # Nakuru
            '/Users/nickj/IPA-data/Nakuru/images/166_Molo_B.pdf/odd-pages/166_Molo_B.pdf-page-3.png',
            '/Users/nickj/IPA-data/Nakuru/images/166_Molo_B.pdf/odd-pages/166_Molo_B.pdf-page-1.png',
            '/Users/nickj/IPA-data/Nakuru/images/174_Bahati.pdf/odd-pages/174_Bahati.pdf-page-099.png',
            '/Users/nickj/IPA-data/Nakuru/images/174_Bahati.pdf/odd-pages/174_Bahati.pdf-page-019.png',
            '/Users/nickj/IPA-data/Nakuru/images/174_Bahati.pdf/odd-pages/174_Bahati.pdf-page-235.png',

            # Narok
            '/Users/nickj/IPA-data/Narok/images/179_Narok North.pdf/even-pages/179_Narok North.pdf-page-080.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-189.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-109.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-017.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-161.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-003.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-061.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-033.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-029.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-027.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-187.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-149.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-123.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-089.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-059.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-159.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-043.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-077.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-107.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-147.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-131.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-025.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-075.png',
            '/Users/nickj/IPA-data/Narok/images/182_Narok West.pdf/odd-pages/182_Narok West.pdf-page-023.png',

            # Siaya
            '/Users/nickj/IPA-data/Siaya/images/234_Alego Usongo_B.pdf/odd-pages/234_Alego Usongo_B.pdf-page-47.png',

            # Taita Taveta
            '/Users/nickj/IPA-data/Taita Taveta/images/025_Mwatate.pdf/odd-pages/025_Mwatate.pdf-page-093.png',
            '/Users/nickj/IPA-data/Taita Taveta/images/025_Mwatate.pdf/odd-pages/025_Mwatate.pdf-page-091.png',

            # Tharaka Nithi
            '/Users/nickj/IPA-data/Tharaka Nithi/images/060_Maara_B.pdf/even-pages/060_Maara_B.pdf-page-116.png',
            '/Users/nickj/IPA-data/Tharaka Nithi/images/060_Maara_B.pdf/even-pages/060_Maara_B.pdf-page-110.png',
            '/Users/nickj/IPA-data/Tharaka Nithi/images/060_Maara_B.pdf/even-pages/060_Maara_B.pdf-page-120.png',
            '/Users/nickj/IPA-data/Tharaka Nithi/images/060_Maara_B.pdf/even-pages/060_Maara_B.pdf-page-166.png',
            '/Users/nickj/IPA-data/Tharaka Nithi/images/060_Maara_B.pdf/even-pages/060_Maara_B.pdf-page-112.png',
            '/Users/nickj/IPA-data/Tharaka Nithi/images/060_Maara_B.pdf/even-pages/060_Maara_B.pdf-page-108.png',
            '/Users/nickj/IPA-data/Tharaka Nithi/images/060_Maara_B.pdf/even-pages/060_Maara_B.pdf-page-074.png',
            "/Users/nickj/IPA-data/Tharaka Nithi/images/061_Igambang'ombe_B.pdf/even-pages/061_Igambang'ombe_B.pdf-page-84.png",
            "/Users/nickj/IPA-data/Tharaka Nithi/images/061_Igambang'ombe_B.pdf/even-pages/061_Igambang'ombe_B.pdf-page-72.png",
            "/Users/nickj/IPA-data/Tharaka Nithi/images/061_Igambang'ombe_B.pdf/even-pages/061_Igambang'ombe_B.pdf-page-94.png",
            "/Users/nickj/IPA-data/Tharaka Nithi/images/061_Igambang'ombe_B.pdf/even-pages/061_Igambang'ombe_B.pdf-page-34.png",
            "/Users/nickj/IPA-data/Tharaka Nithi/images/061_Igambang'ombe_B.pdf/even-pages/061_Igambang'ombe_B.pdf-page-66.png",
            "/Users/nickj/IPA-data/Tharaka Nithi/images/061_Igambang'ombe_B.pdf/even-pages/061_Igambang'ombe_B.pdf-page-58.png",
            "/Users/nickj/IPA-data/Tharaka Nithi/images/061_Igambang'ombe_B.pdf/even-pages/061_Igambang'ombe_B.pdf-page-70.png",
            "/Users/nickj/IPA-data/Tharaka Nithi/images/061_Igambang'ombe_C.pdf/even-pages/061_Igambang'ombe_C.pdf-page-034.png",

            # Trans Nzoia
            '/Users/nickj/IPA-data/Trans Nzoia/images/136_Kwanza.pdf/odd-pages/136_Kwanza.pdf-page-157.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/137_Endebess.pdf/even-pages/137_Endebess.pdf-page-040.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-199.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-117.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-091.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-129.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-157.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-041.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-089.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-125.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-115.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-085.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-069.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-197.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-155.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-127.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-087.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-039.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-081.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-123.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-145.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-013.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-067.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-143.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-079.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/138_Saboti.pdf/odd-pages/138_Saboti.pdf-page-015.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/139_Kiminini.pdf/odd-pages/139_Kiminini.pdf-page-071.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/139_Kiminini.pdf/odd-pages/139_Kiminini.pdf-page-003.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/139_Kiminini.pdf/odd-pages/139_Kiminini.pdf-page-083.png',
            '/Users/nickj/IPA-data/Trans Nzoia/images/139_Kiminini.pdf/odd-pages/139_Kiminini.pdf-page-063.png',

            # Turkana
            '/Users/nickj/IPA-data/Turkana/images/124_Turkana West_A.pdf/odd-pages/124_Turkana West_A.pdf-page-137.png',
            '/Users/nickj/IPA-data/Turkana/images/124_Turkana West_A.pdf/odd-pages/124_Turkana West_A.pdf-page-037.png',
            '/Users/nickj/IPA-data/Turkana/images/124_Turkana West_B.pdf/odd-pages/124_Turkana West_B.pdf-page-39.png',
            '/Users/nickj/IPA-data/Turkana/images/124_Turkana West_C.pdf/odd-pages/124_Turkana West_C.pdf-page-1.png',
            '/Users/nickj/IPA-data/Turkana/images/125_Turkana Central.pdf/odd-pages/125_Turkana Central.pdf-page-057.png',
            '/Users/nickj/IPA-data/Turkana/images/125_Turkana Central.pdf/odd-pages/125_Turkana Central.pdf-page-061.png',
            '/Users/nickj/IPA-data/Turkana/images/125_Turkana Central.pdf/even-pages/125_Turkana Central.pdf-page-062.png',
            '/Users/nickj/IPA-data/Turkana/images/126_Loima.pdf/odd-pages/126_Loima.pdf-page-193.png',
            '/Users/nickj/IPA-data/Turkana/images/126_Loima.pdf/odd-pages/126_Loima.pdf-page-171.png',
            '/Users/nickj/IPA-data/Turkana/images/126_Loima.pdf/odd-pages/126_Loima.pdf-page-153.png',
            '/Users/nickj/IPA-data/Turkana/images/126_Loima.pdf/odd-pages/126_Loima.pdf-page-169.png',
            '/Users/nickj/IPA-data/Turkana/images/126_Loima.pdf/odd-pages/126_Loima.pdf-page-173.png',

            # Uasin Gishu
            '/Users/nickj/IPA-data/Uasin Gishu/images/141_Soy_B.pdf/even-pages/141_Soy_B.pdf-page-084.png',
            '/Users/nickj/IPA-data/Uasin Gishu/images/146_Kesses.pdf/odd-pages/146_Kesses.pdf-page-059.png',

            # Vihiga
            '/Users/nickj/IPA-data/Vihiga/images/211_Vihiga.pdf/odd-pages/211_Vihiga.pdf-page-05.png',
            '/Users/nickj/IPA-data/Vihiga/images/211_Vihiga.pdf/odd-pages/211_Vihiga.pdf-page-03.png',
            '/Users/nickj/IPA-data/Vihiga/images/213_Hamisi.pdf/odd-pages/213_Hamisi.pdf-page-107.png',
            '/Users/nickj/IPA-data/Vihiga/images/213_Hamisi.pdf/odd-pages/213_Hamisi.pdf-page-057.png',

            # West Pokot
            '/Users/nickj/IPA-data/West Pokot/images/129_Kapenguria.pdf/odd-pages/129_Kapenguria.pdf-page-211.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-169.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-179.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-193.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-049.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-175.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-155.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-039.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-191.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-167.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-171.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-247.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-205.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-181.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-037.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-149.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-157.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-121.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-067.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-203.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-147.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-177.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-151.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-119.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-163.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-141.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-047.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-225.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-153.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-245.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-065.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-087.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-145.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-117.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-005.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-159.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-091.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-313.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-007.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-301.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-123.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-113.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-345.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-089.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-223.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-165.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-173.png',
            '/Users/nickj/IPA-data/West Pokot/images/131_Kacheliba.pdf/odd-pages/131_Kacheliba.pdf-page-161.png',
            '/Users/nickj/IPA-data/West Pokot/images/132_Pokot South.pdf/odd-pages/132_Pokot South.pdf-page-345.png',
            '/Users/nickj/IPA-data/West Pokot/images/132_Pokot South.pdf/even-pages/132_Pokot South.pdf-page-346.png',

            # Migori
            '/Users/nickj/IPA-data/Migori/images/255_Suna East.pdf/odd-pages/255_Suna East.pdf-page-087.png',
            '/Users/nickj/IPA-data/Migori/images/255_Suna East.pdf/odd-pages/255_Suna East.pdf-page-065.png',
            '/Users/nickj/IPA-data/Migori/images/255_Suna East.pdf/odd-pages/255_Suna East.pdf-page-049.png',
            '/Users/nickj/IPA-data/Migori/images/255_Suna East.pdf/odd-pages/255_Suna East.pdf-page-081.png',
            '/Users/nickj/IPA-data/Migori/images/255_Suna East.pdf/odd-pages/255_Suna East.pdf-page-093.png',
            '/Users/nickj/IPA-data/Migori/images/255_Suna East.pdf/odd-pages/255_Suna East.pdf-page-009.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_A.pdf/odd-pages/259_Kuria West_A.pdf-page-099.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_A.pdf/odd-pages/259_Kuria West_A.pdf-page-069.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_A.pdf/odd-pages/259_Kuria West_A.pdf-page-067.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_A.pdf/odd-pages/259_Kuria West_A.pdf-page-097.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_A.pdf/odd-pages/259_Kuria West_A.pdf-page-005.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_A.pdf/odd-pages/259_Kuria West_A.pdf-page-021.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_A.pdf/odd-pages/259_Kuria West_A.pdf-page-101.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_A.pdf/odd-pages/259_Kuria West_A.pdf-page-045.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_A.pdf/odd-pages/259_Kuria West_A.pdf-page-023.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_A.pdf/odd-pages/259_Kuria West_A.pdf-page-009.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_A.pdf/odd-pages/259_Kuria West_A.pdf-page-051.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_B.pdf/odd-pages/259_Kuria West_B.pdf-page-57.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_B.pdf/odd-pages/259_Kuria West_B.pdf-page-09.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_B.pdf/odd-pages/259_Kuria West_B.pdf-page-13.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_B.pdf/odd-pages/259_Kuria West_B.pdf-page-53.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_B.pdf/odd-pages/259_Kuria West_B.pdf-page-23.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_B.pdf/odd-pages/259_Kuria West_B.pdf-page-21.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_B.pdf/odd-pages/259_Kuria West_B.pdf-page-19.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_B.pdf/odd-pages/259_Kuria West_B.pdf-page-17.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_B.pdf/odd-pages/259_Kuria West_B.pdf-page-05.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_B.pdf/odd-pages/259_Kuria West_B.pdf-page-55.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_B.pdf/odd-pages/259_Kuria West_B.pdf-page-51.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_B.pdf/odd-pages/259_Kuria West_B.pdf-page-11.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_B.pdf/odd-pages/259_Kuria West_B.pdf-page-15.png',
            '/Users/nickj/IPA-data/Migori/images/259_Kuria West_B.pdf/odd-pages/259_Kuria West_B.pdf-page-07.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-119.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-101.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-129.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-109.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-017.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-085.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-115.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-121.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-021.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-049.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-123.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-005.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-031.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-113.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-081.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-045.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-059.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-087.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-111.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-105.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-003.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-075.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-037.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-089.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-107.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-007.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-093.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-015.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-013.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-097.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-091.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-053.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-073.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-067.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-103.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-033.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-095.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-069.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-001.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-127.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-125.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-131.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-025.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-035.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-029.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-023.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-011.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-019.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-009.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-099.png',
            '/Users/nickj/IPA-data/Migori/images/260_Kuria East.pdf/odd-pages/260_Kuria East.pdf-page-039.png',
    ]

    def __init__(self, full_path, quick_init=False):
        self.full_path = full_path
        if os.path.isfile(self.upload_tracker_file):
            self.data = pickle.load(open(self.upload_tracker_file))
        else:
            self.data = {}
        self.data.setdefault(self.UPLOADED_INSTANCES_KEY, [])
        self.data.setdefault(self.JOB_ID_KEY, None)
        self.data.setdefault(self.UPLOADS_DONE_NAME, False)
        if not quick_init:
            self.initialize_captricity_client()

    @property
    def upload_tracker_file(self):
        return os.path.join(self.full_path, self.UPLOAD_TRACKER_NAME)

    @property
    def job_id(self):
        return self.data.get(self.JOB_ID_KEY)

    @property
    def uploaded_instances(self):
        return self.data.get(self.UPLOADED_INSTANCES_KEY)

    @property
    def api_token(self):
        api_token = os.environ.get('CAPTRICITY_API_TOKEN', None)
        assert api_token is not None, "Define CAPTRICITY_API_TOKEN environment variable."
        return api_token

    @property
    def job_name(self):
        return 'IPA - ' + os.path.basename(os.path.split(self.full_path)[0])

    @property
    def job_uploading_name(self):
        return self.job_name + ' UPLOADING; NOT READY YET'

    @property
    def all_uploads_done(self):
        return self.data.get(self.UPLOADS_DONE_NAME, False)

    def initialize_captricity_client(self):
        self.client = Client(self.api_token)

    def create_captricity_job(self):
        if self.job_id is not None:
            self.save()
            return
        job = self.client.create_jobs({'document_id': self.DOCUMENT_ID})
        self.data[self.JOB_ID_KEY] = job.get('id')
        self._update_job_name(self.job_uploading_name)
        self.save()

    def print_job_info(self):
        print 'Uploading %s pages to to "%s" (https://shreddr.captricity.com/admin/shreddr/job/%s/)' % (self._get_total_pdf_page_count()/2, self.job_name, self.job_id)

    def print_finished_upload_info(self):
        print '\tSanity check URLs:'
        self._get_total_pdf_page_count(sanity=True)
        uploaded_isets = self.client.read_instance_sets(self.job_id)
        print 'Finished uploading %s pages to "%s" (https://shreddr.captricity.com/admin/shreddr/job/%s/)\n' % (len(uploaded_isets), self.job_name, self.job_id)

    def _update_job_name(self, name):
        self.client.update_job(self.job_id, {'name': name})

    def continue_uploads(self):
        assert self.job_id is not None
        image_path = self._get_next_image_upload_path()
        existing_isets = { iset['name']:iset['id']
                           for iset in self.client.read_instance_sets(self.job_id) }
        while image_path is not None:
            iset_name = os.path.basename(image_path)
            if iset_name not in existing_isets:
                iset = self.client.create_instance_sets(self.job_id, {'name':iset_name})
                iset_id = iset['id']
                print '\tUploading %s to Job %s as InstanceSet %s (https://shreddr.captricity.com/admin/shreddr/instanceset/%s/)' % (image_path, self.job_id, iset_name, iset_id)
                assert len(self.client.read_instance_set_instances(iset_id)) == 0
                instance_data = {'page_number':'0', 'image_file':open(image_path, 'rb')}
                self.client.create_instance_set_instances(iset_id, instance_data)
            else:
                iset_id = existing_isets[iset_name]
            assert len(self.client.read_instance_set_instances(iset_id)) == 1, 'Problem with InstanceSet %s' % iset_id
            self.uploaded_instances.append(image_path)
            self.save()
            image_path = self._get_next_image_upload_path()
        self._sanity_check()
        self._update_job_name(self.job_name)
        self.data[self.UPLOADS_DONE_NAME] = True
        self.save()

    def _sanity_check(self):
        image_paths = self._get_all_image_full_paths()
        uploaded_isets = self.client.read_instance_sets(self.job_id)
        total_pages = self._get_total_pdf_page_count()
        assert total_pages/2.0 == len(uploaded_isets), 'Unexpected page counts: %s vs %s' % (total_pages/2.0, len(uploaded_isets))
        uploaded_iset_names = [iset['name'] for iset in uploaded_isets]
        expected_iset_names = [os.path.basename(image_path) for image_path in image_paths]
        uploaded_iset_name_set = set(uploaded_iset_names)
        expected_iset_name_set = set(expected_iset_names)
        assert len(uploaded_iset_names) == len(uploaded_iset_name_set), 'Not all uploaded iset names were unique!'
        assert len(expected_iset_names) == len(expected_iset_name_set), 'Not all expected iset names were unique!'
        assert len(uploaded_iset_names) == len(expected_iset_names), 'Different numbers of uploaded and expected isets: %s vs %s' % (len(uploaded_iset_names), len(expected_iset_names))
        difference = expected_iset_name_set - uploaded_iset_name_set
        assert len(difference) == 0, 'Difference: %s' % difference
        difference = uploaded_iset_name_set - expected_iset_name_set
        assert len(difference) == 0, 'Difference: %s' % difference

    def _get_total_pdf_page_count(self, sanity=False):
        pdf_dir = os.path.split(self.full_path)[0]
        total_count = 0
        for file_name in os.listdir(pdf_dir):
            if not file_name.endswith('.pdf'):
                continue
            pdf_file_path = os.path.join(pdf_dir, file_name)
            page_count = self._get_pdf_file_page_count(pdf_file_path)
            if sanity:
                print '\t\t%s: %s pages.  https://shreddr.captricity.com/admin/shreddr/instance/?instance_set__job__id__exact=%s&p=%s' % (pdf_file_path, page_count, self.job_id, total_count/10)
            total_count += page_count
        return total_count

    def _get_pdf_file_page_count(self, pdf_file_path):
        num_pages = None
        try:
            pdfinfo_output = subprocess.check_output(['pdfinfo', pdf_file_path])
            for tok in pdfinfo_output.split('\n'):
                if tok.find('Pages') < 0: continue
                num_pages_str = tok[tok.find(':')+1:].strip() # it should always reach here
                if num_pages_str.isdigit():
                    num_pages = int(num_pages_str)
                    break
        except subprocess.CalledProcessError:
            num_pages = None
        # PDFs with an odd number of pages *must* be in MODIFIED_PDF_PAGE_COUNTS
        if num_pages is not None and num_pages % 2 != 0:
            num_pages = self.MODIFIED_PDF_PAGE_COUNTS[pdf_file_path]
        num_pages = self.MODIFIED_PDF_PAGE_COUNTS.get(pdf_file_path, num_pages)
        assert num_pages is not None, 'File %s is broken.' % pdf_file_path
        return num_pages

    def _get_next_image_upload_path(self):
        all_image_paths = self._get_all_image_full_paths()
        for image_path in all_image_paths:
            if image_path not in self.uploaded_instances:
                return image_path
        return None

    def _get_all_image_full_paths(self):
        all_images = []
        for pdf_file_name in os.listdir(self.full_path):
            pdf_images_path = os.path.join(self.full_path, pdf_file_name)
            if not os.path.isdir(pdf_images_path):
                continue
            all_images.extend(self._get_pdf_image_full_paths(pdf_images_path))
        return all_images

    def _get_pdf_image_full_paths(self, pdf_images_path):
        # We assume the bigger files are the page we want
        even_dir = os.path.join(pdf_images_path, 'even-pages')
        odd_dir = os.path.join(pdf_images_path, 'odd-pages')
        assert os.path.isdir(even_dir), 'Not a directory: %s' % even_dir
        assert os.path.isdir(odd_dir), 'Not a directory: %s' % odd_dir
        even_files = os.listdir(even_dir)
        odd_files = os.listdir(odd_dir)
        even_files = [os.path.join(pdf_images_path, 'even-pages', f) for f in even_files]
        odd_files = [os.path.join(pdf_images_path, 'odd-pages', f) for f in odd_files]
        if len(odd_files) == 0 or len(even_files) == 0:
            return []
        even_file_sizes = [os.path.getsize(f) for f in even_files if f not in self.FILE_SIZE_SKIP_LIST]
        odd_file_sizes = [os.path.getsize(f) for f in odd_files if f not in self.FILE_SIZE_SKIP_LIST]
        avg_even_size = float(sum(even_file_sizes))/len(even_file_sizes)
        avg_odd_size = float(sum(odd_file_sizes))/len(odd_file_sizes)
        if avg_even_size > avg_odd_size:
            # Should be atleast 512kb different between smallest first page and largest second
            # See Baringo/161_Mogotio_A.pdf missort
            assert min(even_file_sizes) > (max(odd_file_sizes) + self.FILE_SIZE_DIFFERENTIAL), 'Suspect size differential: %s' % even_dir
            return even_files
        elif avg_odd_size > avg_even_size:
            # Should be atleast 512kb different between smallest first page and largest second
            # See Baringo/161_Mogotio_A.pdf missort
            assert min(odd_file_sizes) > (max(even_file_sizes) + self.FILE_SIZE_DIFFERENTIAL), 'Suspect size differential: %s' % odd_dir
            return odd_files
        raise Exception('Could not distinguish files: %s' % pdf_images_path)

    def save(self):
        fout = open(self.upload_tracker_file, 'w')
        pickle.dump(self.data, fout)
        fout.close()

if __name__ == "__main__":
    main()
