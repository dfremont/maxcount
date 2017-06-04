#!/usr/bin/env python

import sys, os, re, argparse, math

verbose = False

def is_soft_clause(line,top_weight):
    wclause = line.split()
    weight = int(wclause[0])
    return top_weight == None or weight < top_weight

def write_soft_clause(line,top_weight,clause_selector,soft_clause_id,random_var,comparator_vars,outstream):
    assert(is_soft_clause(line,top_weight))
    soft_clause_id_tmp = soft_clause_id
    wclause = line.split()
    weight = int(wclause[0])
    outstream.write("-" + str(comparator_vars[weight]) + " ")
    # encode clause id:
    if verbose and False:
        print("\nClause ID " + str(soft_clause_id_tmp))
        # print(clause_selector)
        # print("Length " + str(len(clause_selector)))
        print("c Encoding that clause selector implies bound holds\n")
    for i in range(0,len(clause_selector)):
        if soft_clause_id_tmp % 2 == 1:
            outstream.write("-")
        outstream.write(str(clause_selector[len(clause_selector) - 1 - i]) + " ")
        soft_clause_id_tmp /= 2
    outstream.write("0\n")
    
    if verbose and False:
        print("c Encoding that clause has to hold\n")
    soft_clause_id_tmp = soft_clause_id
    for i in range(0,len(clause_selector)):
        if soft_clause_id_tmp % 2 == 1:
            outstream.write("-")
        outstream.write(str(clause_selector[len(clause_selector) - 1 - i]) + " ")
        soft_clause_id_tmp /= 2
        
    wclause.pop(0)
    for lit in wclause:
        if lit.startswith('0'):
            assert(len(lit) == 1 or not lit[1].isdigit())
            outstream.write("0\n")
        else:
            outstream.write(lit + " ")
        

def lesser_than(consequence, bitvector, constant, outstream, max_var,true_var):
    # if verbose:
    #     print("c Constant to encode " + str(constant))
    #     print("c Think I need this many bits " + str(int(math.ceil(math.log(constant,2)))))
    #     print("c Length of bitvector " + str(len(bitvector)))
    assert(int(math.ceil(math.log(constant,2))) <= len(bitvector))
    helper_var = -true_var
    
    # look at lesser_than.txt
    # building the lesser than gate from the least significant bit to the most significant bit
    for i in range(0,len(bitvector)):
        if constant % 2 == 1:
            max_var += 1
            next_helper_var = max_var
            outstream.write(str(-next_helper_var) + " " + 
                            str(-bitvector[len(bitvector) - 1 - i]) + " " + 
                            str(helper_var) + " 0\n")
            helper_var = next_helper_var
        else:
            # first clause:
            max_var += 1
            next_helper_var = max_var
            outstream.write(str(-next_helper_var) + " " + 
                            str(helper_var) + " 0\n")
            # second clause
            outstream.write(str(-next_helper_var) + " " + 
                            str(-bitvector[len(bitvector) - 1 - i]) + " 0\n")
            # update helper var
            helper_var = next_helper_var
        
        constant //= 2
        
    if consequence: # encoding a comparator, connect to comparator var
        outstream.write(str(consequence) + " " + str(helper_var) + " 0\n")
        outstream.write(str(-consequence) + " " + str(-helper_var) + " 0\n")
    else: # encoding the upper bound on the randoms, must be true no matter what
        outstream.write(str(helper_var) + " 0\n")
    return max_var

def encode(instream,outstream):
    # read the file, find the header
    found_header = False
    for line in instream:
        if line.startswith("p wcnf "):
        # if line[0] == 'p':
            # parse the header
            words = line.split()
            
            if len(words) == 4:
                # maximum total weight missing
                print('c Warning: no top weight given! See standard. Assuming all clauses to be soft.')
                (num_vars,num_clauses,top) = (int(words[2]),int(words[3]), None)
            else: 
                assert len(words) == 5
                (num_vars,num_clauses,top) = (int(words[2]),int(words[3]),int(words[4]))
            found_header = True
            break
        if line[0].isdigit():
            break
            
    if not found_header:
        sys.exit("Error: no header found")
    
    max_var = num_vars
    
    # count soft clauses, determine maximum weight, register all variables
    soft_clause_num = 0
    weight_max = 0
    total_weight = 0
    comparator_vars = dict()
    # variables = set()
    variables_occurring_in_soft_clauses = set()
    for line in instream:
        if line[0].isdigit(): # is a clause
            clause = line.split()
            # be sure maxvar is actually greatest var
            assert( not any(list(map(lambda w: max_var < int(w),clause[1:]))))
            
            if is_soft_clause(line,top):
                soft_clause_num += 1
                weight = int(clause[0])
                total_weight += weight
                if weight not in comparator_vars: 
                    max_var += 1
                    comparator_vars[weight] = max_var
                if weight > weight_max:
                    weight_max = weight
                clause.pop(0)
                for lit in clause:
                    if  not lit.startswith('0'):
                        variables_occurring_in_soft_clauses.add(abs(int(lit)))
            # collect all variables to put in independent support
            # literals = line.split()
            # literals.pop(0)
            # for l in literals:
            #     var = abs(int(l))
            #     if var != 0:
            #         variables.add(var)
    num_weights = max_var - num_vars

    outstream.write("c Found these weights " + str(comparator_vars) + '\n')
    outstream.write("c In total " + str(num_weights) + ' different weights\n')
    outstream.write("c Max weight: " + str(weight_max) + '\n')
    outstream.write("c Total weight: " + str(total_weight) + ' (indicated: ' + str(top) + ')\n')
    
    instream.seek(0) # reset the file handle, could reopen the file if its a performance issue
    
    # create counting vars
    assert(soft_clause_num > 0)
    soft_clause_num_log = int(math.ceil(math.log(soft_clause_num + 1, 2))) 
    clause_selector = dict()
    for i in range(0,soft_clause_num_log):
        max_var += 1
        clause_selector[i] = max_var
    
    if verbose:
        print("c Clause selector vars: " + str(clause_selector))
    
    max_weight_num_log = int(math.ceil(math.log(weight_max + 1,2)))
    assert(max_weight_num_log > 0)
    random_var = dict()
    for i in range(0,max_weight_num_log):
        max_var += 1
        random_var[i] = max_var
    
    # write the prefix
    outstream.write("c variables to maximize over\n")
    outstream.write("c max")
    for v in variables_occurring_in_soft_clauses:
        outstream.write(" " + str(v))
    outstream.write(" 0\n")
    
    outstream.write("c variables selecting soft clauses\n")
    outstream.write("c ind")
    for index,var in clause_selector.items():
        outstream.write(" " + str(var))
    outstream.write(" 0\n")
    
    outstream.write("c variables for random choice\n")
    outstream.write("c ind")
    for index,var in random_var.items():
        outstream.write(" " + str(var))
    outstream.write(" 0\n")
    
    # Determine new maximal variable number, overapproximated?
    new_max_vars = max_var + num_weights * len(random_var) + len(clause_selector) + 1
    
    outstream.write("p cnf " + str(new_max_vars) + " " + str(num_clauses) + "\n")
    
    # find the list of different weights
    soft_clause_id = 0
    for line in instream:
        if not line[0].isdigit(): # is a clause!
            continue
        clause = line.split()
        
        # print("c Clause number " + clause_id + "\n")
        
        if is_soft_clause(line,top):
            write_soft_clause(line, 
                              top,
                              clause_selector,
                              soft_clause_id,
                              random_var,
                              comparator_vars,
                              outstream)
            soft_clause_id += 1
        else: 
            clause.pop(0)
            for lit in clause:
                if lit.startswith('0'):
                    outstream.write('0\n')
                else:
                    outstream.write(lit + ' ')
    max_var += 1
    true_var = max_var
    if verbose:
        outstream.write("c This is the variable constant true:\n")
    outstream.write(str(true_var) + " 0\n")
    
    # encode lesser thans
    for weight,var in comparator_vars.items():
        if verbose:
            outstream.write("c Comparator for weight " + str(weight) + "\n")
        # encode lesser than constraints
        max_var = lesser_than(var, random_var, weight, outstream, max_var, true_var)
    
    outstream.write("c Upper bound for clause selector: " + str(soft_clause_num) + "\n")
    max_var = lesser_than(None, clause_selector, soft_clause_num, outstream, max_var, true_var)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='Print additional output.')
    parser.add_argument('-d', '--directory', dest='directory', action='store', 
                        help='Run all wcnf files from this directory. If no file or directory is specified, read from stdin.')
    parser.add_argument('-f', '--file', dest='file', action='store',  metavar='file', 
                        help='Run specified wcnf file. If no file or directory is specified, read from stdin.')
    parser.add_argument('-o', '--output', dest='output', action='store', 
                        help='Specify output file. Default is stdout.')
    parser.add_argument('-r', '--recursive', action='store_true', 
                        help='Also consider subfolders. Requires option --directory.')
    parser.add_argument('--zipdimacs', type=bool, default=False, help='Zip dimacs files after creation. Requires --output.')
    # parser.add_argument('--timeout', dest='timeout', action='store', default=None,
                        # help='Timeout in seconds (default: None)')
    # parser.add_argument('--threads', dest='threads', action='store', nargs='?', type=int, metavar='num', default=multiprocessing.cpu_count(),
                        # help='Number of threads touse (default: 1)')

    args = parser.parse_args()
    
    if args.directory and args.file:
        sys.exit("Cannot specify both directory and file.")
    if not args.directory and args.recursive:
        sys.exit("Recursive flag requires directory flag.")
    if args.zipdimacs and not args.output and not args.directory:
        sys.exit("zipdimacs flag requires output file or directory input.")
    if args.directory and args.output:
        sys.exit("Flag --directory incompatible with flag --output.")
    
    if args.verbose:
        verbose = True
    
    instream = sys.stdin
    if args.directory:
        # TODO
        sys.exit("Not implemented")
    if args.file:
        instream = open(args.file)
    
    outstream = sys.stdout
    if args.output:
        outstream = open(args.output, 'w')
    
    encode(instream,outstream)

