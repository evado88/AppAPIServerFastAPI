from helpers import assist


def get_validation_members():
    members = []

    index = 0

    for i in range(1, 205):
        pad = str(i).zfill(3)
        padNext = str(i + 1).zfill(3)
        index = i

        members.append(
            {
                # id
                # personal
                "fname": f"Member-{pad}",
                "lname": "Account",
                "dob": assist.get_current_date(),
                "position": "-",
                # id
                "id_type": "NRC",
                "id_no": f"100{pad}/10/1",
                "id_attachment": 2,
                # contact, address
                "email": f"member-{pad}.acount@gmail.com",
                "mobile1": f"260577100{pad}",
                "mobile2": f"260576100{pad}",
                "address_physical": f"Libala Stage {i}, Lusaka",
                "address_postal": f"P.O Box 300{pad}",
                # guarantor
                "guar_fname": f"Member{i+1}",
                "guar_lname": "Account",
                "guar_mobile": f"260577100{padNext}",
                "guar_email": f"member-{padNext}.acount@gmail.com",
                # banking
                "bank_name": "ABSA",
                "bank_branch_name": "Lusaka Business Centre",
                "bank_branch_code": "020016",
                "bank_account_name": f"Member-{pad} Account",
                "bank_account_no": f"1000{pad}",
                # account
                "password": "12345678",
                # approval
                "status_id": 4,
                "stage_id": 8,
                "approval_levels": 2,
                # service
                "created_by": f"member-{pad}.acount@gmail.com",
            }
        )

    index += 1
    pad = str(index).zfill(3)
    padNext = str(index + 1).zfill(3)
    
    members.append(
        {
            # id
            # personal
            "fname": "Osacco",
            "lname": "Account",
            "dob": assist.get_current_date(),
            "position": "-",
            # id
            "id_type": "NRC",
            "id_no": f"100{pad}/10/1",
            "id_attachment": 2,
            # contact, address
            "email": "osacco.acount@gmail.com",
            "mobile1": f"260577100{pad}",
            "mobile2": f"260576100{pad}",
            "address_physical": f"Libala Stage {i}, Lusaka",
            "address_postal": f"P.O Box 300{pad}",
            # guarantor
            "guar_fname": "Osawe",
            "guar_lname": "Account",
            "guar_mobile": f"260577100{padNext}",
            "guar_email": "osawe.acount@gmail.com",
            # banking
            "bank_name": "ABSA",
            "bank_branch_name": "Lusaka Business Centre",
            "bank_branch_code": "020016",
            "bank_account_name": f"Osacco Account",
            "bank_account_no": f"1000{pad}",
            # account
            "password": "12345678",
            # approval
            "status_id": 4,
            "stage_id": 8,
            "approval_levels": 2,
            # service
            "created_by": "osacco.acount@gmail.com",
        }
    )
    
    index += 1
    pad = str(index).zfill(3)
    padNext = str(index + 1).zfill(3)
    
    members.append(
        {
            # id
            # personal
            "fname": "Osawe",
            "lname": "Account",
            "dob": assist.get_current_date(),
            "position": "-",
            # id
            "id_type": "NRC",
            "id_no": f"100{pad}/10/1",
            "id_attachment": 2,
            # contact, address
            "email": "osawe.acount@gmail.com",
            "mobile1": f"260577100{pad}",
            "mobile2": f"260576100{pad}",
            "address_physical": f"Libala Stage {i}, Lusaka",
            "address_postal": f"P.O Box 300{pad}",
            # guarantor
            "guar_fname": "Osacco",
            "guar_lname": "Account",
            "guar_mobile": f"260577100{padNext}",
            "guar_email": "osacco.account@gmail.com",
            # banking
            "bank_name": "ABSA",
            "bank_branch_name": "Lusaka Business Centre",
            "bank_branch_code": "020016",
            "bank_account_name": "Osawe Account",
            "bank_account_no": f"1000{pad}",
            # account
            "password": "12345678",
            # approval
            "status_id": 4,
            "stage_id": 8,
            "approval_levels": 2,
            # service
            "created_by": "osawe.acount@gmail.com",
        }
    )

    return members


def get_validation_admins():
    members = [
        {
            # id
            # personal
            "fname": "Adam",
            "lname": "Lwendo",
            "position": "ICT Specialist",
            # contact, address
            "email": "adam.lwendo@hotmail.com",
            "mobile": "26077123451",
            "address_physical": "Silverest, Lusaka",
            "address_postal": "P.O Box 30578",
            # account
            "role": 2,
            "password": "12345678",
            # approval
            "status_id": 4,
            "stage_id": 8,
            "approval_levels": 2,
            # service
            "created_by": "adam.lwendo@hotmail.com",
        },
        {
            # id
            # personal
            "fname": "Akim",
            "lname": "Liseli",
            "position": "ICT Systems Administrator",
            # contact, address
            "email": "akim.liseli@hotmail.com",
            "mobile": "26077123452",
            "address_physical": "Northmead, Lusaka",
            "address_postal": "P.O Box 30058",
            # account
            "role": 2,
            "password": "12345678",
            # approval
            "status_id": 4,
            "stage_id": 8,
            "approval_levels": 2,
            # service
            "created_by": "akim.liseli@hotmail.com",
        },
        {
            # id
            # personal
            "fname": "Alice",
            "lname": "Sinyama",
            "position": "Networks Specialist",
            # contact, address
            "email": "alice.sinyama@hotmail.com",
            "mobile": "26077123453",
            "address_physical": "Waterfalls, Lusaka",
            "address_postal": "P.O Box 30971",
            # account
            "role": 2,
            "password": "12345678",
            # approval
            "status_id": 4,
            "stage_id": 8,
            "approval_levels": 2,
            # service
            "created_by": "alice.sinyama@hotmail.com",
        },
    ]

    return members
