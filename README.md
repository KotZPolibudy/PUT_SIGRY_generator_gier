# PUT_SIGRY_generator_gier

Druga część projektu ma charakter eksperymentalny. W przypadku trudności z uzyskaniem działającego generatora questów, należy opisać przetestowane podejścia i napotkane problemy w raporcie. W projekcie można korzystać z dowolnego modelu językowego (sugerowane jest użycie modeli lokalnych, takich jak Qwen3.6 np. korzystając z Ollama).

Projekt wykonywany jest grupach trzy- lub czteroosobowych. W raporcie należy jednoznacznie wskazać podział pracy na osoby.


Raport powinien składać się z czterech elementów: 

kod generatora fabuł
folder zawierający definicję przynajmniej jednej serii questów (pliki json / pddl)
kod odgrywający fabuły
raport podsumowujący projekt
Projekt należy przesłać do 08.06.26, godzina 23:59. Ocena z części 2.2 stanowi 60% oceny z drugiego projektu. Zaliczenie części 2.2 nie jest konieczne do zaliczenia drugiego projektu.
Szczegółowe wymagania opisane są poniżej:


Kod generatora fabuł

Fabuła wygenerowana przez algorytm powinna być spójna i możliwe angażująca dla gracza. Warto wykorzystać tu idee struktury dramatycznej i monomitu.

Generator fabuł powinien generować serię questów składających się na historię zainspirowaną krótkim opisem fabuły podanym na wstępie

Dla każdego questa należy stworzyć plik pddl / json

Definicja świata modelu pddl powinna być wspólna dla wszystkich questów i zaprojektowana osobiście. Każda akcja możliwa do wykonania w grze powinna być reprezentowana przez odpowiednią akcję STRIPS. 

Plik pddl powinien zawierać definicję zadania planowania, którego rozwiązanie jest przebiegiem questa. Definicja questa powinna być oparta na stanie początkowym zadania planowania. Quest powinien być zdefiniowany serią predykatów opisujących możliwe interakcje w ramach questu. 

Plik jsona powinien zawierać listę obiektów występujących w queście razem z krótkim ich opisem. W przypadku użycia postaci, json powinien zawierać ponadto wszystkie dialogi postaci.

Generator powinien przetestować wykonalność każdego z questów korzystając z solvera STRIPS. 

W przypadku wygenerowania questa którego nie da się ukończyć, bądź którego plan wykonania odbiega od zamierzonej fabuły questa, należy zaimplementować mechanizm starający się naprawić go.

Jeżeli nie uda się stworzyć skutecznego generatora questów, należy opisać napotkane problemy w raporcie.

Przynajmniej jedna działająca seria questów (json, pddl) wygenerowana przy wykorzystaniu zaproponowanego generatora fabuł, razem z oryginalnym promptem.

Jeżeli nie uda się stworzyć skutecznego generatora questów, należy opisać napotkane problemy w raporcie, oraz zawrzeć w nim działającą definicję questów, z zaznaczonymi zmianami wprowadzonymi względem wyniku działania generatora.

Kod odgrywający fabuły

Kod wykorzystujący pliki json i pddl i umożliwiający odegranie serii questów

Wystarczy zaimplementować interfejs tekstowy. Interfejs powinien pozwalać na wykonywanie wszystkich akcji możliwych w danym momencie (podnoszenie przedmiotów, rozmowa z NPC, walka z wrogami, przejście do innych lokacji itp.) i pokazywać istotne informacje, takie jak zawartość ekwipunku, opis lokacji i postaci, dialogi itp.

Dla ambitnych - można dodać elementy graficzne generowane modelami dyfuzyjnymi w oparciu o opisy zawarte w pliku json. W takim wypadku, należy dostarczyć kod generujący prompt oraz same prompty które posłużyły do generacji grafik.

Raport opisujący ideę stojącą za zaproponowaną metodą generacji questów, wraz z dyskusją problemów napotkanych po drodze oraz wad i zalet użytej metody / promptów.
