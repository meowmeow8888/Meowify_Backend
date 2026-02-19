class Baa:
    def __init__(self):
        self.meow = 1
        self.bla = "nariw"
        self.apweo = False

b = Baa()
print(" ".join(b.__dict__.keys()))