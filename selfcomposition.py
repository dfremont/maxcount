#!/usr/bin/env python3

# Usage to get k-fold sc:    ./selfcomposition.py k filename

import sys
    
def sign(num):
    if num > 0: return 1
    else: return -1

def lesser_or_equal(consequence, bv1, bv2, newlines, next_fresh):
    
    assert (len(bv1) == len(bv2))
    bitwidth = len(bv1)
    
    helper_var = next_fresh
    next_fresh += 1
    newlines.append(str(helper_var) + ' 0\n')
    
    # building the lesser gate from the least significant bit to the most significant bit
    for i in range(0,len(bv1)):
        
        next_helper_var = next_fresh
        next_fresh += 1
        index = bitwidth - 1 - i
        
        # first clause
        newlines.append(str(-bv1[index]) + " " +
                        str(-next_helper_var) + " " + 
                        str(-bv2[index]) + " " + 
                        str(helper_var) + " 0\n")
        
        # second clause:
        newlines.append(str(bv1[index]) + " " +
                        str(-next_helper_var) + " " + 
                        str(helper_var) + " 0\n")
        # third clause
        newlines.append(str(bv1[index]) + " " +
                        str(-next_helper_var) + " " + 
                        str(-bv2[index]) + " 0\n")
        # update helper var
        helper_var = next_helper_var
        
    if consequence: # encoding a comparator, connect to comparator var
        newlines.append(str(-consequence) + " " + str(helper_var) + " 0\n")
        newlines.append(str(consequence) + " " + str(-helper_var) + " 0\n")
    else: # encoding the upper bound on the randoms, must be true no matter what
        newlines.append(str(helper_var) + " 0\n")
    return next_fresh, newlines

def not_equal(bv1, bv2, newlines, next_fresh):
    
    assert (len(bv1) == len(bv2))
    bitwidth = len(bv1)
    
    diff_bits = list(range(next_fresh, next_fresh + bitwidth))
    next_fresh += bitwidth
    
    for (i, diff_bit) in enumerate(diff_bits):
        # first clause
        newlines.append(str(-bv1[i]) + " " +
                        str(-bv2[i]) + " " + 
                        str(-diff_bit) + " 0\n")
        
        # second clause:
        newlines.append(str(bv1[i]) + " " +
                        str(bv2[i]) + " " + 
                        str(-diff_bit) + " 0\n")
        
    # require at least one bit difference
    clause = " ".join(str(bit) for bit in diff_bits)
    clause += " 0\n"
    newlines.append(clause)

    return next_fresh, newlines

if __name__ == "__main__":
    
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print ("Usage: " + sys.argv[0] + " [--enforce_order] [--enforce_unequal] integer filename\n")
        quit()

    args = sys.argv
    order = False
    unequal = False
    args.pop(0) # program name
    
    if '--enforce_order' in args:
        print ("c Detected --enforce_order option")
        args.remove('--enforce_order')
        order = True
    if '--enforce_unequal' in args:
        print("c Detected --enforce_unequal option")
        args.remove('--enforce_unequal')
        unequal = True
    
    k = int(args[0])
    assert(k>0)
    filename = args[1]
    
    print ("c Reading file " + filename)

    with open(filename, 'r') as myfile:
        lines = myfile.readlines()
        newlines = []
        maxvars = set()
        countvars = set()
    
        seen_header = False
    
        print ("c Building " + str(k) + "-fold quantitative self-composition...")
    
        added_clauses = 0
        var_copy_map = dict() # maps variables to lists of copies
    
        for line in lines:
            # make UV and EV comments and remember them
            if line.startswith('c max'):
                newlines.append('c ind ' + line.lstrip('c max'))
                words = line.split()
                words.pop(0) # leading 'c'
                words.pop(0) # leading 'max'
                words.pop() # trailing '0'
                maxvars.update(set(map(int,words)))
                assert(0 not in maxvars)
            elif line.startswith('c ind'):
                words = line.split()
                assert(len(words)>2)
                lastelem = words.pop()
                for elem in words[2:]:
                    countvars.add(int(elem))
                newlines.append('c previous ind: ' + line.lstrip('c ind'))
            elif line.startswith('p cnf '):
                # parse header
                words = line.split()
                var_num = int(words[2])
                next_fresh_var = var_num + 1
            
                #assert(len(maxvars.intersection(countvars)) == 0)
                for var in maxvars:
                    if var in countvars:
                        countvars.remove(var)
            
                countvarlist = sorted(list(countvars))
                new_countvarlist = []
                # for v in countvarlist:
                #     fresh_vars = list(range(next_fresh_var,next_fresh_var+(k-1)))
                #     countvar_map[v] = fresh_vars
                #     next_fresh_var += k-1
                #     new_countvarlist.append(v)
                #     new_countvarlist += fresh_vars
                
                for v in list(range(1,var_num+1)):
                    if v not in maxvars:
                        # print('c adding var ' + str(v))
                        fresh_vars = list(range(next_fresh_var,next_fresh_var+(k-1)))
                        assert(0 not in fresh_vars)
                        var_copy_map[v] = fresh_vars
                        next_fresh_var += k-1
                        if v in countvars:
                            new_countvarlist.append(v)
                            new_countvarlist += fresh_vars
                
                if len(countvarlist) * k != len(new_countvarlist):
                    print ('Error: new_countvarlist does not have expected length: ' + str(len(countvarlist) * k) + ' vs ' + str(len(new_countvarlist)))
                    assert(False)
            
                # ind_line = 'c ind ' + ' '.join(str(x) for x in new_countvarlist) + ' 0\n'
                ind_line = 'c ind ' + ' '.join(map(str, new_countvarlist)) + ' 0\n'
                newlines.append(ind_line)

                clause_num = int(words[3])
                next_fresh_var += 1 # better safe than sorry
                maximal_var_index = next_fresh_var
                if order:
                    maximal_var_index += (k-1) * (len(countvars) + 1)
                    # print ('Have ' + str(len(countvars)) + ' countvars')
                    clause_num += (k-1) * (3 * len(countvars) + 2)
                elif unequal:
                    num_pairs = k * (k-1) // 2
                    maximal_var_index += num_pairs * len(countvars)
                    clause_num += num_pairs * (2 * len(countvars) + 1)
                
                newlines.append('p cnf ' + str(maximal_var_index) + ' ' + str(clause_num) + '\n')
            
                if order:
                    # newlines.append('c Starting with order constraints\n')
                    for i in list(range(0,k-1)):
                        bv1 = []
                        bv2 = []
                        for v in countvars:
                            copies_of_v = var_copy_map[v]
                            assert(len(copies_of_v) == k-1)
                            if i == 0:
                                bv1.append(v) # revenge of premature optimization
                            else:
                                bv1.append(copies_of_v[i-1])
                            bv2.append(copies_of_v[i])
                        next_fresh_var,newlines = lesser_or_equal(None, bv1, bv2, newlines, next_fresh_var)
                elif unequal:
                    # newlines.append('c Inequality constraints:\n')
                    for i in range(k-1):
                        for j in range(i+1,k):
                            bv1 = []
                            bv2 = []
                            for v in countvars:
                                copies_of_v = var_copy_map[v]
                                assert(len(copies_of_v) == k-1)
                                if i == 0:
                                    bv1.append(v) # revenge of premature optimization
                                else:
                                    bv1.append(copies_of_v[i-1])
                                bv2.append(copies_of_v[j-1])
                            next_fresh_var, newlines = not_equal(bv1, bv2, newlines, next_fresh_var)
            
                seen_header = True
            
            else:
                if line.startswith('c '):
                    if not seen_header:
                        newlines.append(line)
                    # otherwise skip
                else:
                    assert(seen_header)
                    words = line.split()
                    literals = list(map(int,words))
                    if len(literals) > 0: 
                        literals.pop()
                        newlines.append(line)
                        # print ('detected these literals: ' + str(literals))
                        if any(map(lambda x: not abs(x) in maxvars, literals)): 
                            # print('found a clause with countvar: ' + line)
                            # is a clause to be copied
                    
                            for i in list(range(0,k-1)):
                                added_clauses += 1
                                newclause = []
                                for l in literals:
                                    if abs(l) not in maxvars:
                                        l_map = var_copy_map[abs(l)]
                                        newclause.append(sign(l) * l_map[i])
                                    else:
                                        newclause.append(l)
                                newclause.append(0)
                                newclause_string = ' '.join(list(map(str,newclause))) + '\n'
                                # print('adding the following: ' + newclause_string)
                                newlines.append(newclause_string)
    
    
        header_found = False
        for idx,line in enumerate(newlines):
            if line.startswith('p cnf'):
                header_found = True
                words = line.split()
                # var_num = int(words[2])
                clause_num = int(words[3])
                clause_num += added_clauses
                newlines[idx] = 'p cnf ' + words[2] + ' ' + str(clause_num) + '\n'
            
        assert(header_found)
            
        if (maxvars == None):
            print('Error: no variables to maximize over found (start line with \'c max\')')
            assert(False)
    
        if seen_header:
            sys.stdout.write(''.join(newlines))
    