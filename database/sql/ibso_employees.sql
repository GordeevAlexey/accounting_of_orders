SELECT 
    A1_1.C_EMAIL email,
    A1_1.C_NAME user_name
FROM
    Z#ACC_PHONEBOOK A1_1,
    Z#DEPART A2_1,
    Z#CASTA A3_1
WHERE
    A1_1.C_DEPART = A2_1.ID(+)
    AND A1_1.C_CASTA = A3_1.ID(+)
    AND A1_1.C_EMAIL is not null
    AND A1_1.C_NAME is not null
    AND A1_1.C_EMAIL != '-'