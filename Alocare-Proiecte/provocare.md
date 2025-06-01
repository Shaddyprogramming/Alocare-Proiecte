	Scriptul de alocare proiecte in momentul de fata nu este optim 
din punct de vedere: al timpului de executie, alocarea tine cont 
de ordinea optiunilor si nu ia in calcul toate optiunile pentru o 
alocare completa.

Trebuie sa respecte cateva reguli:

		1.In fiecare grupa nu pot fi doua echipe cu teme din acelasi
	domeniu.
		2.Daca sunt mai mult de o echipa cu prima optiune in acelasi 
	domeniu, se declara una din echipe castigatoare intr-un mod 
	randomizat. ( se foloseste un “seed” de randomizare pentru a 
	avea aceleasi rezultate la fiecare rulare) 
		3.Dupa alocarea din runda 1 (prima optiune) se trece la runda 2,
	respectiv 3 (daca este cazul)
		4.Unde nu are ce aloca va marca echipa respectiva corespunzator. 
	Alocarea temelor pentru respectivele echipe ramane in sarcina 
	tutorilor.