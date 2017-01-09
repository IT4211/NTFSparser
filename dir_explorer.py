#-*- coding: utf-8 -*-

import pytsk3
import _dir_explorer

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

    def __init__(self, volume = "\\\\.\\PhysicalDrive0"):
        localvolume = volume
        localvolumehandle = pytsk3.Img_Info(localvolume)
        partitionTable = pytsk3.Volume_Info(localvolumehandle)
        self._recursive = False

        for partition in partitionTable:
            # LG 노트북 Basic data partition
            # 2048 섹터의 내용은 무조건 건너뛰게?
            if ('NTFS' in partition.desc) or(('Basic data partition' in partition.desc) and (7 == partition.addr)):
                print partition.desc, partition.addr
                self._fs_info = pytsk3.FS_Info(localvolumehandle, offset=(partition.start * 512))

    def list_directory(self, directory, stack=None):
        stack.append(directory.info.fs_file.meta.addr)

        for directory_entry in directory:
            prefix = "+" * (len(stack) - 1)
            if prefix:
                prefix += " "

            # Skip ".", ".." or directory entries without a name.
            if (not hasattr(directory_entry, "info") or
                    not hasattr(directory_entry.info, "name") or
                    not hasattr(directory_entry.info.name, "name") or
                        directory_entry.info.name.name in [".", ".."]):
                continue

            self.print_directory_entry(directory_entry, prefix=prefix)

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
            path = "/"
        elif inode_or_path.startswith("/"):
            path = inode_or_path
        else:
            inode = inode_or_path

        # Note that we cannot pass inode=None to fs_info.opendir().
        if inode:
            directory = self._fs_info.open_dir(inode=inode)
        else:
            directory = self._fs_info.open_dir(path=path)

        return directory

    def print_directory_entry(self, directory_entry, prefix=""):
        meta = directory_entry.info.meta
        name = directory_entry.info.name

        name_type = "-"
        if name:
            name_type = self.FILE_TYPE_LOOKUP.get(int(name.type), "-")

        meta_type = "-"
        if meta:
            meta_type = self.META_TYPE_LOOKUP.get(int(meta.type), "-")

        directory_entry_type = "{0:s}/{1:s}".format(name_type, meta_type)

        for attribute in directory_entry:
            inode_type = int(attribute.info.type)
            if inode_type in self.ATTRIBUTE_TYPES_TO_PRINT:
                if self._fs_info.info.ftype in [
                    pytsk3.TSK_FS_TYPE_NTFS, pytsk3.TSK_FS_TYPE_NTFS_DETECT]:
                    inode = "{0:d}-{1:d}-{2:d}".format(
                        meta.addr, int(attribute.info.type), attribute.info.id)
                else:
                    inode = "{0:d}".format(meta.addr)

                attribute_name = attribute.info.name
                if attribute_name and attribute_name not in ["$Data", "$I30"]:
                    filename = "{0:s}:{1:s}".format(name.name, attribute.info.name)
                else:
                    filename = name.name

                if meta and name:
                    print("{0:s}{1:s} {2:s}:\t{3:s}".format(
                        prefix, directory_entry_type, inode, filename))


#fls 처럼 구현하되, 결과물에 타임 정보와 html 파일 생성기!
if __name__=='__main__':

    dir_path = _dir_explorer.ParseCommandLine()
    dir_explorer = dir_explorer()
    directory = dir_explorer.open_directory(dir_path)
    dir_explorer.list_directory(directory, [])
