import time
import random

def get_list(x=20, y=3):
    lista = random.sample(xrange(x), y)
    listb = random.sample(xrange(x), y)
    return lista, listb

def intersect(la, lb):
    def member(x):
        return x in lb
    return filter(member, la)


def intersect2(la, lb):
    return [i for i in la if i in lb]

def intersect3(la, lb):
    return [i for i in la if i in set(lb)]

a = time.time()
res = {}
for i in xrange(10**5):
    res[i] = True
res = res.keys()

b = time.time() - a
print b

a = time.time()

res = set([i for i in xrange(10**5) if i % 4])
print time.time() - a

# a = time.time()
# for i in xrange(10**5):
#     lista, listb = get_list()
#     filter(lambda x: x in listb, lista)
# print time.time() - a - b
#
# a = time.time()
# for i in xrange(10**5):
#     lista, listb = get_list()
#     list(set(lista) & set(listb))
# print time.time() - a - b
#
# a = time.time()
# for i in xrange(10**5):
#     lista, listb = get_list()
#     [i for i in lista if i in listb]
# print time.time() - a - b
#
# a = time.time()
# for i in xrange(10**5):
#     lista, listb = get_list()
#     [i for i in lista if i in set(listb)]
# print time.time() - a - b
#
# a = time.time()
# for i in xrange(10**5):
#     lista, listb = get_list()
#     intersect2(lista, listb)
# print time.time() - a - b
#
#
# a = time.time()
# for i in xrange(10**5):
#     lista, listb = get_list()
#     intersect3(lista, listb)
# print time.time() - a