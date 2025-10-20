import random

print('hello')
def group_distribution_simulation(
    members,
    months=6,
    contribution_range=(50, 200),
    loan_range=(100, 500)
):
    """
    Simulate multiple months of group contributions and direct member-to-member loan payments.
    Tracks cumulative totals for each member and carries forward balances/shortfalls.
    """
    records = []
    running_balance = 0  # carry-over balance
    member_totals = {m: {"contributed": 0, "received": 0} for m in members}

    for month in range(1, months + 1):
        # --- Step 1: Generate random contributions and loan requests ---
        contributions = {m: random.randint(*contribution_range) for m in members}
        
        
        applicants = random.sample(members, random.randint(1, len(members)))
        loan_requests = {m: random.randint(*loan_range) for m in applicants}

        # --- Step 2: Initialize for matching ---
        lenders = {m: amount for m, amount in contributions.items()}
        borrowers = {m: amount for m, amount in loan_requests.items()}
        distribution = []
        
        lender_list = list(lenders.items())
        borrower_list = list(borrowers.items())
        
    
        lender_idx = borrower_idx = 0

        # --- Step 3: Match contributors to borrowers ---
        while lender_idx < len(lender_list) and borrower_idx < len(borrower_list):
            lender, available = lender_list[lender_idx]
            borrower, needed = borrower_list[borrower_idx]

            if available == 0:
                lender_idx += 1
                continue
            if needed == 0:
                borrower_idx += 1
                continue

            transfer = min(available, needed)
            distribution.append({"from": lender, "to": borrower, "amount": transfer})

            # update balances
            lenders[lender] -= transfer
            borrowers[borrower] -= transfer

            # update member totals
            member_totals[lender]["contributed"] += transfer
            member_totals[borrower]["received"] += transfer

            if lenders[lender] == 0:
                lender_idx += 1
            if borrowers[borrower] == 0:
                borrower_idx += 1

        # --- Step 4: Compute monthly totals ---
        total_contributions = sum(contributions.values())
        total_requested = sum(loan_requests.values())
        total_distributed = sum(t["amount"] for t in distribution)
        balance = total_contributions - total_distributed + max(running_balance, 0)
        shortfall = total_requested - total_distributed + abs(min(running_balance, 0))

        # --- Step 5: Update running balance ---
        running_balance = balance - shortfall

        status = "✅ Fully funded" if shortfall <= 0 else "⚠️ Shortfall"

        # --- Step 6: Store record ---
        records.append({
            "month": month,
            "contributions": contributions,
            "loan_requests": loan_requests,
            "distribution_list": distribution,
            "total_contributions": total_contributions,
            "total_requested": total_requested,
            "total_distributed": total_distributed,
            "month_balance": max(balance, 0),
            "shortfall": max(shortfall, 0),
            "running_balance": running_balance,
            "status": status
        })

    # --- Step 7: Compute final member summary ---
    member_summary = {
        m: {
            "total_contributed": member_totals[m]["contributed"],
            "total_received": member_totals[m]["received"],
            "net_position": member_totals[m]["received"] - member_totals[m]["contributed"]
        }
        for m in members
    }

    return {"months": records, "members": member_summary}


# Example usage
members = ["Alice", "Bob", "Cathy", "David", "Eve"]
simulation = group_distribution_simulation(members, months=1)

# --- Display results ---
for r in simulation["months"]:
    print(f"\n📅 Month {r['month']} - {r['status']}")
    print(f"  Total Contributions: ${r['total_contributions']}")
    print(f"  Total Requested: ${r['total_requested']}")
    print(f"  Total Distributed: ${r['total_distributed']}")
    print(f"  Balance: ${r['month_balance']}")
    print(f"  Shortfall: ${r['shortfall']}")
    print(f"  Running Balance: ${r['running_balance']}")
    print("  Distribution List:")
    for d in r["distribution_list"]:
        print(f"    {d['from']} → {d['to']}: ${d['amount']}")

print("\n📊 --- Cumulative Member Summary ---")
for m, s in simulation["members"].items():
    print(f"{m}: Contributed ${s['total_contributed']}, Received ${s['total_received']}, Net ${s['net_position']}")
