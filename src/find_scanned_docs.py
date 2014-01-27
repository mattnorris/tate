#! /usr/local/bin/python
# Title:        find_scanned_docs.py
#
# Description:  Traverses a source directory. If PDFs are found, copy them
#               to the target directory. If no PDF is found, copy all files to
#               the target directory.
#
#               (This was the convention I used when
#               uploading my scanned notes to Evernote: if a directory had a
#               PDF, it meant I combined all relevant JPEGs into a PDF, so just
#               upload that. If I didn't, I want to upload *all* of the JPEGs.)
#
#               In this case, the target directory is a synced Evernote
#               directory for uploading files in bulk.
#
# Author:       Matthew Norris
# References:   http://seagullcanfly.posterous.com/syncing-a-local-folder-to-evernote

import os
import shutil

# TODO: These could be input from the command line.
source_dir = 'D:\Documents\gallery_download'
target_dir = 'D:\Documents\upload'

def getFiles(currentDir):
    """
    Returns a list of files to copy.
    """
    files = []
    # Walk directory tree starting at the given directory.
    for root, dirs, files in os.walk(currentDir):
        # Reset the flags for each directory.
        contains_pdf = False
        pdfs = []
        jpgs = []

        # Go through each file.
        for f in files:
            # If you find a PDF, you'll be grabbing PDF files.
            fext = os.path.splitext(f)[1].lower()
            if fext == '.pdf':
                contains_pdf = True
                pdfs.append((root, f))
            # Otherwise get the JPEGs.
            elif fext == '.jpeg' or fext == '.jpg':
                jpgs.append((root, f))

        # Prepare the files (if any) to copy.
        if contains_pdf and pdfs:
            print '"%s" contains PDF files. Copy only PDFs.' % root
            print 'Copying %d PDF files.' % len(pdfs)
            files += pdfs
        elif jpgs:
            print '"%s" contains only JPEG files. Copy all of them.' % root
            print 'Copying %d JPEG files.' % len(jpgs)
            files += jpgs
        else:
            print 'No files found in "%s"' % root

    return files

# TODO: Implement a "dryrun" parameter.
def main():
    """
    Copy PDFs and JPEGs from the source directory.
    """
    print 'Scanning "%s"...\n' % target_dir
    files = getFiles(source_dir)
    print '\nPreparing to copy %d files to "%s"...' % (len(files), target_dir)

    for fileinfo in files:
        filepath = os.path.join(fileinfo[0], fileinfo[1])
        print '.',
        shutil.copy(filepath, target_dir)

    print '\nDone.'

if __name__ == "__main__":
    main()