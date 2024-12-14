def run():
    """
    ----------------------------------------
    Jeu de la bataille (jeu de 32 cartes)
    Les fichiers image des cartes sont placés sous le répertoire
    '/home/sitebj/portail/images/ImagesCartes'
    ---------------------------------------
    """
    import random
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    from matplotlib.patches import Rectangle
    import streamlit as st
    import json
    import os

    # ------------------------------
    def regles():
        # Toutes les règles dans une seule chaîne HTML
        html_content = """
        <p style='color: blue; margin-bottom: 0px;'>Cliquer sur 'Nouveau tirage' pour faire apparaître 2 nouvelles cartes</p>
        <p style='color: blue; margin-bottom: 0px;'>Les barres bleue représentent le nombre de cartes que chaque joueur a en mains</p>
        <p style='color: blue; margin-bottom: 0px;'>Les barres orange le nombre de cartes de chaque joueur 'sur la table'</p>
        <br>
        """

        # Affiche de tout le contenu HTML dans un seul appel de st.markdown
        st.markdown(html_content, unsafe_allow_html=True)
        
    #----------------    
    def distribuer(paq):
        # distribution alternée du paquet de cartes 'paq'
        paq1 = [paq[i] for i in range(0,32,2)] # distribution au joueur 1 
        paq2 = [paq[i] for i in range(1,32,2)] # distribution au joueur 2 
        return paq1, paq2
    
    # ------------------------------
    def carte(lst):
    # liste des cartes à partir de leur positions indiquées dans lst
       liste = []
       for i in range(len(lst)):
           liste.append(cartes[lst[i]-1]) 
       return liste 
   
    # ------------------------------
    def permute(lst,n):
    # permutation circulaire vers la droite de n élément de la liste lst    
        if (n >= len(lst)):
            return lst
        else:
            for i in range(n):
                lst = lst[-1:] + lst[:-1]  # on prend le dernier élément (-1) que l'on met en 1ère position et on continue
            return lst
        
    # ---------------------------
    def affiche(c1,c2,h1,h2,t1,t2):
    # affichage des cartes c1 et c2)
    # h1, h2 = nombre de cartes de chaque joueur (pour fixer hauteur du rectangle)
    # t1, t2 = nombre de cartes des tas 1 et 2 (pour fixer hauteur du rectangle)
        fich = racine + cartes[c1-1] + ".gif"
        img1 = mpimg.imread(fich)
        fich = racine + cartes[c2-1] + ".gif"
        img2 = mpimg.imread(fich)
        
        # figure avec 4 sous-graphes
        fig, (ax11, ax12, ax21, ax22) = plt.subplots(1, 4, figsize=(10, 5))
        ax11.axis('off') 
        ax12.axis('off') 
        ax21.axis('off') 
        ax22.axis('off')

        # paquet joueur 1    
        rect = Rectangle((0.12, 0.), 0.5, h1/32, edgecolor='blue', facecolor='skyblue')
        ax11.add_patch(rect)
        rect = Rectangle((0.7, 0.), 0.25, t1/32, edgecolor='orange', facecolor='orange')
        ax11.add_patch(rect)
        ax11.set_title(str(h1))
        
        # carte joueur 1
        ax12.imshow(img1)
        ax12.set_title('joueur 1')

        # carte joueur 2
        ax21.imshow(img2)
        ax21.set_title('joueur 2')
        
        # paquet joueur 2    
        rect = Rectangle((0.05, 0.), 0.25, t2/32, edgecolor='orange', facecolor='orange')
        ax22.add_patch(rect)
        rect = Rectangle((0.38, 0.), 0.5, h2/32, edgecolor='blue', facecolor='skyblue')
        ax22.add_patch(rect)
        ax22.set_title(str(h2))

        # Affichage de la figure
        st.pyplot(fig)   
            
    # ---------------------------  
    def sauver(lst,nom_lst,dossier_sauvegarde="."):
    # sauvegarde de la liste lst comme fichier de nom 'nom_lst.json
        fich = os.path.join(dossier_sauvegarde, nom_lst)  # nom du fichier correspondant à la liste 'lst'
        try:    
            with open(fich,'w') as fichier:
                json.dump(lst,fichier)
            #st.success(f"La liste {nom_lst} a été sauvegardée avec succès dans {fich}")
        except Exception as e:
            st.error(f"Une erreur s'est produite lors de la sauvegarde de {nom_lst}: {e}") 
            
    # ---------------------------
    def restaurer(nom_lst,dossier_sauvegarde="."):          
    # restauration du fichier de nom 'nom_lst.json dans la liste 'lst
        fich = os.path.join(dossier_sauvegarde, nom_lst)  # nom du fichier correspondant à la liste 'lst'     
        try:    
            with open(fich,'r') as fichier:
                lst = json.load(fichier) 
            #st.success(f"La liste {nom_lst} a été restaurée avec succès depuis {fich}")
            return lst  
        except Exception as e:
            st.error(f"Une erreur s'est produite lors de la restauration de {nom_lst}: {e}")

    # ------------------------------------------ 
    # programme principal
    cartes = ['7','8','9','10','valet','dame','roi','as']
    st.markdown("<h2 style='color: orange;'>Jeu de la bataille</h2>", unsafe_allow_html=True)
    regles()
    # chemin pour stockage/restauration des listes 'paq' et 'tas' entre 2 itérations
    chemin = "/home/sitebj/portail/projets/prov"
    # emplacement des fichiers images des cartes
    racine = "/home/sitebj/portail/images/ImagesCartes/"  # répertoire de stockage des images
    nbitermax = 200

    # initialisation
    if 'iteration' not in st.session_state:
        st.session_state.iteration = 0
        jeu = list(range(1,9)) 
        paq = jeu*4 # paquet de 32 cartes constitués de 4 jeux (trèfle, carreau, coeur, pique)
        random.shuffle(paq) # paquet 'battu'  

        paq1, paq2 = distribuer(paq) # paquets de chaque joueur après distribution 1 sur 2
        # tas1 et tas2 représentent les cartes tirées par les joueurs 
        tas1 = [] # liste des positions dans paq1 des cartes tirées pour joueur 1
        tas2 = [] # liste des positions dans paq2 des cartes tirées pour joueur 2
            
        # sauvegarde
        sauver(paq1,"paq1.json",chemin)
        sauver(paq2,"paq2.json",chemin)
        sauver(tas1,"tas1.json",chemin)
        sauver(tas2,"tas2.json",chemin)
        

    # Bouton d'incrémentation de l'itération
    if st.button('Nouveau tirage'):
        st.session_state.iteration += 1 
        st.write(f"iteration : {st.session_state.iteration}")
        nbiter = st.session_state.iteration
        
        # restauration
        paq1 = restaurer("paq1.json",chemin)
        paq2 = restaurer("paq2.json",chemin)
        tas1 = restaurer("tas1.json",chemin)
        tas2 = restaurer("tas2.json",chemin)
        
        len1 = len(paq1)
        len2 = len(paq2)
        if (len1 + len2 != 32 ): st.write("problème, somme des 2 paquets non égale à 32")
        n = len(tas1)
        pos1 = len1-1-n # position de la carte à sortir de paq1
        pos2 = len2-1-n # position de la carte à sortir de paq2
        if (pos1 <0 or pos2 <0):
            st.write(f"Le joueur {(lambda pos1, pos2: 2 if pos1 < 0 else 1 if pos2 < 0 else None)(pos1, pos2)} a gagné en {nbiter-1} coup(s), l'autre joueur ne disposant plus de carte à placer")    
        else:        
            c1 = paq1[pos1] # joueur 1 sort la carte c1 (dernière de la liste = celle du dessus)
            tas1.append(pos1) # le tas de joueur 1 s'incrémente
            c2 = paq2[pos2] # joueur 2 sort la carte c2 (dernière de la liste = celle du dessus)
            tas2.append(pos2) # le tas de joueur 2 s'incrémente
            
            # affichage des 2 cartes et des paquets et tas
            affiche(c1,c2,len1,len2,len(tas1),len(tas2))
            
            if (c1 != c2): # un joueur ramasse le tout
                p = 2 * (n + 1) # nombre d'éléments dans tas1 + tas2
                if (c1 > c2): # joueur 1 emporte tas2
                    for pos in tas2:
                        paq1.append(paq2[pos]) # paq1 prend une carte de tas2
                        paq2.pop(pos) # que paq2 perd
                    # on met les éléments de tas1 et tas2 sous le paquet paq1
                    paq1 = permute(paq1,p)
                else:  # joueur 2 emporte tas1
                    for pos in tas1:
                        paq2.append(paq1[pos])
                        paq1.pop(pos)
                    # on met les éléments de tas1 et tas2 sous le paquet paq2
                    paq2 = permute(paq2,p)    
            
                # sauvegarde
                sauver(paq1,"paq1.json",chemin)
                sauver(paq2,"paq2.json",chemin)

                # on vide les tas
                tas1 = []
                tas2 = [] 
                sauver(tas1,"tas1.json",chemin)
                sauver(tas2,"tas2.json",chemin)
                len1 = len(paq1)
                len2 = len(paq2)
                if len1 == 0 or len2 == 0:
                    st.write(f"Le joueur {(lambda l1, l2: 2 if l1 == 0 else 1 if l2 == 0 else None)(len1, len2)} a gagné en {nbiter} coup(s)")
            else: # bataille! tas1 et tas2 restent en place
                sauver(tas1,"tas1.json",chemin)
                sauver(tas2,"tas2.json",chemin)
                    
        if (nbiter > nbitermax): st.write(f"Jeu toujours pas terminé au bout de {nbitermax} coups !")  
            
            
    # Bouton pour réinitialiser le jeu
    if st.button('Relancer le jeu'):
        st.session_state.clear()
        
    # Relance du portail            
    url = "https://courspython.org"
    st.markdown(f"<a href={url} target='_self'>Cliquez ici pour relancer le portail</a>", unsafe_allow_html=True)
    
            
# Si l'application est lancée directement (en dehors du portail), lancer l'application
if __name__ == "__main__":
    run()  
