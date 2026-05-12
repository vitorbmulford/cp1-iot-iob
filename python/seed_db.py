import database


def main():
    database.seed_default_students()
    print("Banco inicializado em:")
    print(database.DB_PATH)
    print("\nAlunos cadastrados:")
    for aluno in database.list_students():
        status = "ativo" if aluno["ativo"] else "inativo"
        print(
            f"- {aluno['nome']} | UID {aluno['uid']} | "
            f"{aluno['exercicio']} | {aluno['repeticoes']} reps | {status}"
        )


if __name__ == "__main__":
    main()
