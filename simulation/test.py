
import random

#lit of all members
print('1-----------------------------------------------------------------')
all_members = ['a', 'b', 'c']

contributions = {m: random.randint(*(3, 7)) for m in all_members}
#contributions = {'a': 10, 'b': 31, 'c': 59}

print('contribtions', contributions)
#contribtions {'a': 206, 'b': 243, 'c': 109, 'd': 272, 'e': 142}     

#members applying for loans this month

no_applicants = random.randint(1, len(all_members))
#no_applicants = 3

print('Total members', len(all_members), ' Applicants', no_applicants)
#Total members 5  Applicants 2

applicants = random.sample(all_members, no_applicants)
#applicants = ['c', 'a']

#print('actual borrowers', applicants)
#actual borrowers ['a', 'c']

loan_requests = {m: random.randint(*(3, 9)) for m in applicants}
#loan_requests = {'b': 5, 'c': 4, 'a': 4}
                 
print('loan request', loan_requests)  
#loan request {'a': 118, 'c': 107}              

#print('2-----------------------------------------------------------------') 

contributions_items = contributions.items()
#print('contributions_items', contributions_items) 

lenders = {m: amount for m, amount in contributions_items}
#print('lenders', lenders)    

loan_requests_items = loan_requests.items()
#print('loan_requests_items', loan_requests_items)

borrowers = {m: amount for m, amount in loan_requests.items()}
#print('borrowers', borrowers)    

print('3-----------------------------------------------------------------')

distribution = []
   
lender_list = list(lenders.items())
borrower_list = list(borrowers.items())
        
lender_idx = borrower_idx = 0
member_totals = {m: {"initial": 0, "loan": 0, "contributed": 0, "received": 0, "saving-balance": 0, "loan-balance": 0} for m in all_members}

for b in range(len(borrower_list)) :
    #get borrower
    borrower = borrower_list[b][0]
    
    for l in range(len(lender_list)):
        #get lender
        lender = lender_list[l][0]
        
        if borrower == lender:
            continue
        
        if borrowers[borrower] == 0:
            continue
        
        if lenders[lender] == 0:
            continue
        
        #print('b:', borrower, 'l', lender)
        
        transfer = min(lenders[lender], borrowers[borrower])
        distribution.append((f"{lender}->{borrower}", transfer))

        # update balances
        lenders[lender] -= transfer
        borrowers[borrower] -= transfer

        # update member totals
        member_totals[lender]["contributed"] += transfer
        member_totals[borrower]["received"] += transfer
  

for key, value in member_totals.items():
    member_totals[key]['initial'] = contributions[key]
    
    if key in loan_requests:
       member_totals[key]['loan'] = loan_requests[key]
       member_totals[key]['loan-balance'] =  loan_requests[key] - value['received']
    else:
       member_totals[key]['loan'] = 0
       member_totals[key]['loan-balance'] =0
       
    member_totals[key]['saving-balance'] =  contributions[key] - value['contributed']

    
        # --- Step 4: Compute monthly totals ---
total_contributions = sum(contributions.values())
total_requested = sum(loan_requests.values())
total_distributed = sum(t[1] for t in distribution)
total_loan_balance = sum(member_totals[m]['loan-balance'] for m in member_totals)
saving_loan_balance = sum(member_totals[m]['saving-balance'] for m in member_totals)

print('total_contributions=', total_contributions)
print('total_requested=', total_requested)
print('total_distributed=', total_distributed)
print('distribution=',distribution)
print('total_loan_balance=', total_loan_balance)
print('saving_loan_balance=', saving_loan_balance)

for key, value in member_totals.items():
    print('-----------------------------------------------------------------------------------------------------------------------')
    print('name:', key, ', initial=', contributions[key],', contribution=', value['contributed'], ', loans received=', value['received'], ', loans requested=', value['loan'],', loans balance=', value['loan-balance'],', saving balance=', value['saving-balance'])



