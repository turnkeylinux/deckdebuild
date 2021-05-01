import sys

def usage(doc):
    def decor(print_syntax):
        def wrapper(err=None):
            if err:
                print("error: %s" % err, file=sys.stderr)
            print_syntax()
            if doc:
                print(doc.strip(), file=sys.stderr)
            sys.exit(1)
        return wrapper
    return decor


        
    
