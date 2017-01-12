#!/usr/bin/env python
"""Sorts through .jpg image files"""

import os
import re
import sys


###############################################################################
# Class: Group: Group


class Group(object):
    def __init__(self, listvals):
        self.lv = listvals


###############################################################################
# Class: SubGroup


class Subgroup(object):
    # def __init__(self, values, step):
    def __init__(self, values, step=0):
        self.vals = sorted(values)
        self.step = step

    def pretty_print(self, pad=0):
        len_vals = len(self.vals)

        frange = "%0*d" % (pad, self.vals[0])

        if len_vals == 1:
            return frange

        if len_vals == 2:
            frange += ",%0*d" % (pad, self.vals[-1])

        else:
            frange += "-%0*d" % (pad, self.vals[-1])
            diff = self.vals[1] - self.vals[0]
            if diff > 1:
                frange += "x%d" % diff

        return frange


###############################################################################
# EXPORTED METHODS


def integerize(in_list):
    '''
    v = 0
    while v < len(inlist):
        inlist[v] = int(inlist[v])
        v += 1
    '''

    # A few different approaches ...
    # 1. Easy to understand ...
    '''
    out_list = []
    for input in in_list:
        out_list.append(int(input))
    '''
    # 2. "list comprehension" ...
    out_list = sorted(int(x) for x in in_list)

    return out_list


def group(numeric_list, paddgroups):
    # It's probably best to *ensure* that the list is sorted numerically
    # in this method; I mean ... you never know, right?
    '''
    v = 0
    w = 0
    testlist = []

    if len(numeric_list) > 1:
        diff = numeric_list[v + 1] - numeric_list[v]
        while v < (len(numeric_list) - 1):
            testdiff = diff
            diff = numeric_list[v + 1] - numeric_list[v]
            if testdiff == diff:
                testlist[w] = numeric_list[v]
                w += 1
            else:
                testlist = [x for x in testlist if x is not None]
                testlist.extend([numeric_list[v]])
                if len(testlist) < 3:
                    testlist = [None] * MAXIMGS
                else:
                    paddgroups[v] = Subgroup(testlist, testdiff)
                    testlist = [None] * MAXIMGS
                w = 0
            v += 1
        return paddgroups
    else:
        return numeric_list
    '''

    len_nums = len(numeric_list)
    if len_nums < 3:
        return numeric_list

    current_nums = set()
    last_diff = 0
    for ii in xrange(len_nums - 1):
        nums = numeric_list[ii:ii + 2]
        diff = nums[1] - nums[0]
        if not last_diff:
            last_diff = diff

        if last_diff != diff:
            paddgroups.append(Subgroup(current_nums))
            last_diff = 0
            current_nums = set([nums[1]])

        else:
            current_nums.update(nums)

    if current_nums:
        paddgroups.append(Subgroup(current_nums))

    print "padd:", paddgroups
    return paddgroups


def simplifylist(groups, allvars):
    w = 0
    while w < len(groups):
        allvars = set(allvars).difference(groups[w].vals)
        w += 1
    return sorted(allvars)


def padfunc(value, padding):
    strvalue = str(value)
    length = len(strvalue)
    while length < (padding + 1):
        strvalue = "0" + strvalue
        length = len(strvalue)
    return strvalue


def printfunc(subgroups, intlist, padding):
    w = 0
    if len(subgroups) > 0:
        sys.stdout.write(files[0][0:namelength + 1])
        while w < len(subgroups):

            sys.stdout.write(padfunc(subgroups[w].vals[0], padding))
            sys.stdout.write('-')
            sys.stdout.write(padfunc(subgroups[w].vals[-1], padding))
            if subgroups[w].step != 1:
                sys.stdout.write("x")
                sys.stdout.write(str(subgroups[w].step))
            if w < len(subgroups) or simplifylist(subgroups, intlist) > 0:
                sys.stdout.write(',')
            w += 1
        w = 0
        intlist = simplifylist(subgroups, intlist)
        while w < len(intlist):
            sys.stdout.write(padfunc(intlist[w], padding))
            if w < len(intlist) - 1:
                sys.stdout.write(',')
            w += 1
        sys.stdout.flush()
        print ".jpg"


def sortfunc(values, padding):
    i = 0
    w = 0
    outputlist = [None] * MAXIMGS
    values = [x for x in values if x is not None]
    while i < len(values):
        if len(values[i]) == (padding + 1):
            outputlist[w] = num_list[i]
            w += 1
        i += 1
    return outputlist


if __name__ == "__main__":
    current_path = os.getcwd()

    i = 0
    temp_list = []
    none_groups = []
    one_groups = []
    two_groups = []
    three_groups = []

    for root, dir_names, file_names in os.walk(current_path):
        # NEVER use the word file (it's actually a command!)
        for file_name in file_names:
            # TODO: Too precise; you need to be able to deal with other
            # suffixes.
            if file_name.endswith(".jpg"):
                temp_list.append(file_name)
    '''
    num_list = temp_list[:]
    i = 0
    k = len(num_list)

    while i < k:
        num_list[i] = num_list[i][4:-4]
        i += 1
    '''
    # TODO: Okay, Mr C-Man, here's a more pythonic way to do this.
    fexpr = re.compile("^.*\.(\d+)\.[^\.]+")
    num_list = []

    for file_name in temp_list:
        fmatch = fexpr.match(file_name)
        if fmatch:
            num_list.append(fmatch.group(1))

    # Working on Making ths sorting below better
    '''
    i = 0
    j = 0
    r = 0
    m = 0
    n = 0
    '''

    # TODO: Way too precise. Try using a dictionary with pad length as the
    # index, a la
    #    frames = {0: [], 1: [], 2: []}

    none_list = []
    one_list = []
    two_list = []
    three_list = []

    # Sort all the file numbers into the levels of padding
    for num in num_list:
        len_num = len(num)
        # if len(num_list[i]) == 1 or num_list[i][0] != '0':
        if len_num == 1 or num[0] != '0':
            none_list.append(num)
            # j += 1
        elif len_num == 2:
            one_list.append(num)
            # r += 1
        elif len_num == 3:
            two_list.append(num)
            # m += 1
        else:
            three_list.append(num)
            # n += 1
        # i += 1

        # Create lists of the integer values in each level of padding
        # none_list_ints = sorted(integerize(none_list[0:j]))
    none_list_ints = integerize(none_list)
    one_list_ints = integerize(one_list)
    two_list_ints = integerize(two_list)
    three_list_ints = integerize(three_list)

    # i = 0
    # Create lists of Subgroup objects for each level of padding
    none_subgroups = group(none_list_ints, none_groups)
    one_subgroups = group(one_list_ints, one_groups)
    two_subgroups = group(two_list_ints, two_groups)
    three_subgroups = group(three_list_ints, three_groups)

    print none_list_ints, ",".join(x.pretty_print(0) for x in none_subgroups)
    print one_list_ints, ",".join(x.pretty_print(1) for x in one_subgroups)
    print two_list_ints, ",".join(x.pretty_print(2) for x in two_subgroups)
    print three_list_ints, ",".join(x.pretty_print(3) for x in three_subgroups)

    # You can figure out the rest from here. :D

    # Find the file name:
    namelength = files[0].index('.')

    # Print the files in each padding group
    printfunc(none_subgroups, none_list_ints, 0)
    printfunc(one_subgroups, one_list_ints, 1)
    printfunc(two_subgroups, two_list_ints, 2)
    printfunc(three_subgroups, three_list_ints, 3)

    raw_input('Enter to finish')
