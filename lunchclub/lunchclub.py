import random
import collections


def secret_algorithm(users, min_group_size=3, previous_matches=None):
    total_users = len(users)
    number_of_groups = total_users // min_group_size
    departments = Departments.from_dict(users, previous_matches)
    
    lunch_groups = LunchGroup.populate_initially(number_of_groups, departments)
 
    # this loop keeps popping a person from a department and adding to
    # a group one by one. So run until no one is left in all departments
    while not all(dept.empty for dept in departments):
        lunch_group = LunchGroup.random_smallest(lunch_groups)
        member = pick_member(departments, lunch_group)
        lunch_group.add(member)
    return lunch_groups


def pick_member(departments, lunch_group):
    largest_to_smallest = list(reversed(sorted(departments, key=len)))
    for dept in largest_to_smallest:
        if dept.name in lunch_group.departments or dept.empty:
            continue
        return dept.choose_optimal(lunch_group)
    # there's no available departments so we have to pick a redundant department
    return largest_to_smallest[0].choose_optimal(lunch_group)


class Member:
    
    def __init__(self, username, department):
        self.username = username
        self.department = department
        self.previous_matches = {}
    
    def to_string(self):
        return self.username + '|' + self.department

    def add_previous_matches(self, matches):
        for dt, username in matches:
            self.previous_matches[username] = dt

    @classmethod
    def from_list(cls, usernames, department):
        return [cls(user, department) for user in usernames]

    
class LunchGroup:
    
    def __init__(self, members=None):
        self.members = members or []
    
    @property
    def departments(self):
        return set([m.department for m in self.members])

    def add(self, member):
        self.members.append(member)
    
    def to_string(self, show_department=True):
        if show_department:
            members = [m.to_string() for m in self.members]
        else:
            members = [m.username for m in self.members]
        return '\t'.join(members)
    
    @classmethod
    def populate_initially(cls, number_groups_to_init, departments):
        groups = []
        for _ in range(number_groups_to_init):
            largest = Departments.pick_largest(departments)
            member = largest.pop()
            lunch_group = cls()
            lunch_group.add(member)
            groups.append(lunch_group)
        return groups
    
    @classmethod
    def random_smallest(cls, groups):
        smallest_size = min(len(g) for g in groups)
        smallest_groups = [g for g in groups if len(g) == smallest_size]
        return random.choice(smallest_groups)

    def __len__(self):
        return len(self.members)

    def __iter__(self):
        return iter(self.members)


class Departments:
    
    def __init__(self, name, members=None):
        self.name = name
        self.members = members
    
    def pop(self):
        random.shuffle(self.members)
        return self.members.pop()

    def choose_optimal(self, lunch_group):
        member_scores = {}
        for member in self.members:
            score = 0
            for lunchmember in lunch_group.members:
                if member.username in lunchmember.previous_matches:
                    score += 1
            member_scores[member] = score

        best_score = min(v for v in member_scores.values())
        # occurrences with lowest
        candidate_members = [m for m, score in member_scores.items() if score == best_score]
        chosen_member = random.choice(candidate_members)
        self.members = [m for m in self.members if m != chosen_member]
        return chosen_member

    @property
    def empty(self):
        return len(self.members) == 0
    
    @classmethod
    def pick_smallest(cls, departments):
        return list(sorted(departments, key=len))[0]
    
    @classmethod
    def pick_largest(cls, departments):
        return list(sorted(departments, key=len))[-1]
    
    @classmethod
    def from_dict(cls, members, previous_matches=None):
        """Members should be a mapping from username -> department"""
        inverted = {}
        for user, dept in members.items():
            if dept not in inverted:
                inverted[dept] = []
            inverted[dept].append(user)

        departments = []
        for dept, member_names in inverted.items():
            members = Member.from_list(member_names, dept)
            if previous_matches is not None:
                for m in members:
                    if m.username in previous_matches:
                        m.add_previous_matches(previous_matches[m.username])
            departments.append(cls(dept, members))
        return departments
    
    def __len__(self):
        return len(self.members)


