from stableset import OrderedSet, StableSet, StableSetEq

stable_sets = [StableSet]
stableeq_sets = [StableSetEq]
ordered_sets = [OrderedSet]

# from ordered_set import OrderedSet as OrderedSet2
# ordered_sets += [OrderedSet2]
# from orderedset import OrderedSet as OrderedSet3
# ordered_sets += [OrderedSet3]

set_and_stable_sets = [set] + stable_sets
stableeq_and_ordered_sets = stableeq_sets + ordered_sets
stable_and_ordered_sets = stable_sets + stableeq_sets + ordered_sets
sets_and_stable_sets = [set] + stable_sets + stableeq_sets
all_sets = [set] + stable_sets + stableeq_sets + ordered_sets
