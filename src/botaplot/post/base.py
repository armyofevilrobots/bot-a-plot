from botaplot.util.util import distance


class BasePost(object):

    def post_lines_to_file(self, lines, filename):
        raise NotImplemented


    def write_lines_to_fp(self, lines, gc):
        raise NotImplemented
