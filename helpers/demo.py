from helpers import assist


def get_demo_members():
    members = [
        {
            # id
            # personal
            "fname": "Mary",
            "lname": "Banda",
            "dob": assist.get_current_date(),
            "position": "Business Lady",
            # id
            "id_type": "NRC",
            "id_no": "148976/11/3",
            "id_attachment": 2,
            # contact, address
            "email": "mary.banda@gmail.com",
            "mobile1": "260977123451",
            "mobile2": "260976123451",
            "address_physical": "Kabwata, Lusaka",
            "address_postal": "P.O Box 34578",
            # guarantor
            "guar_fname": "Mike",
            "guar_lname": "Munalula",
            "guar_mobile": "260977123452",
            "guar_email": "mike.munalula@gmail.com",
            # banking
            "bank_name": "ABSA",
            "bank_branch_name": "Lusaka Business Centre",
            "bank_branch_code": "020016",
            "bank_account_name": "Mary Banda",
            "bank_account_no": "1580914",
            # account
            "password": '12345678',
            # approval
            "status_id": 4,
            "stage_id": 8,
            "approval_levels": 2,
            # service
            "created_by": "mary.banda@gmail.com",
        },
        {
            # id
            # personal
            "fname": "Mike",
            "lname": "Munalula",
            "dob": assist.get_current_date(),
            "position": "Businessman",
            # id
            "id_type": "NRC",
            "id_no": "168976/11/3",
            "id_attachment": 2,
            # contact, address
            "email": "mike.munalula@gmail.com",
            "mobile1": "260977123452",
            "mobile2": "260976123452",
            "address_physical": "Libala, Lusaka",
            "address_postal": "P.O Box 38578",
            # guarantor
            "guar_fname": "Max",
            "guar_lname": "Chibuye",
            "guar_mobile": "260977123453",
            "guar_email": "max.chibuye@gmail.com",
            # banking
            "bank_name": "FNB",
            "bank_branch_name": "Acacia Premier Branch",
            "bank_branch_code": "260039",
            "bank_account_name": "Mike Munalula",
            "bank_account_no": "157788580914",
            # account
            "password": '12345678',
            # approval
            "status_id": 4,
            "stage_id": 8,
            "approval_levels": 2,
            # service
            "created_by": "mike.munalula@gmail.com",
        },
        {
            # id
            # personal
            "fname": "Max",
            "lname": "Chibuye",
            "dob": assist.get_current_date(),
            "position": "Accountant",
            # id
            "id_type": "NRC",
            "id_no": "248976/10/1",
            "id_attachment": 2,
            # contact, address
            "email": "max.chibuye@gmail.com",
            "mobile1": "260977123453",
            "mobile2": "260976123453",
            "address_physical": "Chilenje, Lusaka",
            "address_postal": "P.O Box 39578",
            # guarantor
            "guar_fname": "Gary",
            "guar_lname": "Daka",
            "guar_mobile": "260955123453",
            "guar_email": "gary.daka@yahoo.com",
            # banking
            "bank_name": "ZANACO",
            "bank_branch_name": "Civic Centre",
            "bank_branch_code": "263001",
            "bank_account_name": "Max Chibuye",
            "bank_account_no": "11354545580914",
            # account
            "password": '12345678',
            # approval
            "status_id": 4,
            "stage_id": 8,
            "approval_levels": 2,
            # service
            "created_by": "max.chibuye@gmail.com",
        },
    ]

    return members


def get_demo_admins():
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
