import argparse
import os

def ParseCommandLine():
    parser = argparse.ArgumentParser('dir_explorer')

    parser.add_argument('-p', '--path',
                        help = "Specify the folder name to search",
                        required = True, type=ValidateDirPath)

    global gl_args

    gl_args = parser.parse_args()

    return gl_args.path

def ValidateDirPath(DirPath):
    if not os.path.exists(DirPath):
        raise argparse.ArgumentTypeError('DirPath does not exist')

    if os.access(DirPath, os.R_OK):
        return DirPath
    else:
        raise argparse.ArgumentTypeError('DirPath is not readable')