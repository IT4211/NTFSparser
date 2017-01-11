#-*- coding: utf-8 -*-

import pytsk3
import time
import _dir_explorer
import render_html

class dir_explorer():

    FILE_TYPE_LOOKUP = {
        pytsk3.TSK_FS_NAME_TYPE_UNDEF: "-",
        pytsk3.TSK_FS_NAME_TYPE_FIFO: "p",
        pytsk3.TSK_FS_NAME_TYPE_CHR: "c",
        pytsk3.TSK_FS_NAME_TYPE_DIR: "d",
        pytsk3.TSK_FS_NAME_TYPE_BLK: "b",
        pytsk3.TSK_FS_NAME_TYPE_REG: "r",
        pytsk3.TSK_FS_NAME_TYPE_LNK: "l",
        pytsk3.TSK_FS_NAME_TYPE_SOCK: "h",
        pytsk3.TSK_FS_NAME_TYPE_SHAD: "s",
        pytsk3.TSK_FS_NAME_TYPE_WHT: "w",
        pytsk3.TSK_FS_NAME_TYPE_VIRT: "v"}

    META_TYPE_LOOKUP = {
        pytsk3.TSK_FS_META_TYPE_REG: "r",
        pytsk3.TSK_FS_META_TYPE_DIR: "d",
        pytsk3.TSK_FS_META_TYPE_FIFO: "p",
        pytsk3.TSK_FS_META_TYPE_CHR: "c",
        pytsk3.TSK_FS_META_TYPE_BLK: "b",
        pytsk3.TSK_FS_META_TYPE_LNK: "h",
        pytsk3.TSK_FS_META_TYPE_SHAD: "s",
        pytsk3.TSK_FS_META_TYPE_SOCK: "s",
        pytsk3.TSK_FS_META_TYPE_WHT: "w",
        pytsk3.TSK_FS_META_TYPE_VIRT: "v"}

    ATTRIBUTE_TYPES_TO_PRINT = [
        pytsk3.TSK_FS_ATTR_TYPE_NTFS_IDXROOT,
        pytsk3.TSK_FS_ATTR_TYPE_NTFS_DATA,
        pytsk3.TSK_FS_ATTR_TYPE_DEFAULT]

    def __init__(self):

        self.output = render_html.html_result()
        localvolume = pytsk3.Img_Info(r"\\.\C:")
        self._recursive = False
        self._fs_info = pytsk3.FS_Info(localvolume)


    def list_directory(self, directory, stack=None):
        stack.append(directory.info.fs_file.meta.addr)

        for directory_entry in directory:

            # Skip ".", ".." or directory entries without a name.
            if (not hasattr(directory_entry, "info") or
                    not hasattr(directory_entry.info, "name") or
                    not hasattr(directory_entry.info.name, "name") or
                        directory_entry.info.name.name in [".", ".."]):
                continue

            self.print_directory_entry(directory_entry)

            if self._recursive:
                try:
                    sub_directory = directory_entry.as_directory()
                    inode = directory_entry.info.meta.addr

                    # This ensures that we don't recurse into a directory
                    # above the current level and thus avoid circular loops.
                    if inode not in stack:
                        self.list_directory(sub_directory, stack)

                except IOError:
                    pass

        stack.pop(-1)

    def open_directory(self, inode_or_path):
        inode = None
        path = None
        if inode_or_path is None:
            path = "C:"
        elif inode_or_path.startswith("C"):
            path = inode_or_path[3:]
        else:
            inode = inode_or_path

        # Note that we cannot pass inode=None to fs_info.opendir().
        if inode:
            directory = self._fs_info.open_dir(inode=inode)
        else:
            directory = self._fs_info.open_dir(path=path)

        return directory

    def print_directory_entry(self, directory_entry):
        meta = directory_entry.info.meta
        name = directory_entry.info.name

        if type(meta) != pytsk3.TSK_FS_META:
            return

        filename = (name.name).decode('utf-8').encode('utf-8')
        mtime = time.ctime(meta.mtime)
        atime = time.ctime(meta.atime)
        ctime = time.ctime(meta.crtime)
        etime = time.ctime(meta.ctime)

        #TODO : Modifying the expression of the result value

        for attribute in directory_entry:
            inode_type = int(attribute.info.type)
            if inode_type in self.ATTRIBUTE_TYPES_TO_PRINT:
                if meta and name:
                    self.output.insert_tablerow("1", filename, "path", mtime, atime, ctime, etime)




if __name__=="__main__":
    dir_path = _dir_explorer.ParseCommandLine()
    output = render_html.html_result()
    dir_explorer = dir_explorer()
    directory = dir_explorer.open_directory(dir_path)
    dir_explorer.list_directory(directory, [])
    dir_explorer.output.output()