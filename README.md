# Purpose

This script splits apart a bunch of large PDF files.  Mulitprocessedly.  Uses pdftocairo for high quality conversion.


# Directory Structure

Assume pdfA.pdf, pdfB.pdf, and pdfC.pdf have 4 pages each. Starting structure:

```
_
  \_ split_pdfs.py
  \_ NoPDFFolder
     \_ randomImage.png
  \_ FolderA
     \_ pdfA.pdf
     \_ pdfB.pdf
  \_ FolderB
     \_ pdfC.pdf
     \_ randomFile.txt
```

After running, you'll end up with the following structure:

```
_
  \_ split_pdfs.py
  \_ NoPDFFolder
     \_ randomImage.png
  \_ FolderA
     \_ pdfA.pdf
     \_ pdfB.pdf
     \_ images
        \_ pdfA.pdf
           \_ even-pages
              \_ pdfA.pdf-page-2.png
              \_ pdfA.pdf-page-4.png
           \_ odd-pages
              \_ pdfA.pdf-page-1.png
              \_ pdfA.pdf-page-3.png
        \_ pdfB.pdf
           \_ even-pages
              \_ pdfB.pdf-page-2.png
              \_ pdfB.pdf-page-4.png
           \_ odd-pages
              \_ pdfB.pdf-page-1.png
              \_ pdfB.pdf-page-3.png
  \_ FolderB
     \_ pdfC.pdf
     \_ randomFile.txt
     \_ images
        \_ pdfC.pdf
           \_ even-pages
              \_ pdfC.pdf-page-2.png
              \_ pdfC.pdf-page-4.png
           \_ odd-pages
              \_ pdfC.pdf-page-2.png
              \_ pdfC.pdf-page-4.png
     
```
