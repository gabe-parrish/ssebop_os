import glob, os, shutil
import fnmatch

def reset(dirpath):
    scratchdir = dirpath + os.sep + 'scratch'
    for file in glob.iglob(os.path.join(scratchdir, "*", "*.gz")): #"*" is for subdirectory
        if fnmatch.fnmatch(file, '*.gz'): 
            print file[:-7]
            shutil.move(file, dirpath)
    for file in glob.iglob(os.path.join(dirpath, "Backup", "*.gz")):
        if fnmatch.fnmatch(file, '*.gz'):  #skips over scratch folder
            print file[:-7]
            shutil.move(file, dirpath)
def delete(folder1,folder2):
    os.chdir(dirpath)
    shutil.rmtree(dirpath + os.sep + folder1)
    shutil.rmtree(dirpath + os.sep + folder2)
dirpath = raw_input('Enter filepath:')
reset(dirpath)
delete('scratch','Outputs')