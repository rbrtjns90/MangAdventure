from os.path import splitext, join


def _rename_file(old, new): return new + splitext(old)[-1]


def _uploader(filename, newname, subdirs):
    return join(join(*subdirs), _rename_file(filename, newname))


def cover_uploader(instance, filename):
    return _uploader(filename, 'cover', ['series', instance.slug])


__all__ = ['cover_uploader']

