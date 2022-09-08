-- Пользователи (Полный список), неуволенные сотрудники, исключает
-- технологические учетки 
SELECT
    C_2 system_name,
    C_3 department_code,
    C_4 division,
    C_5 position,
    C_9 private_person
FROM
    IBS.VW_CRIT_USER
where C_11 is null and C_9 is not null order by C_9