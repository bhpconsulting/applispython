# -*- coding: utf-8 -*-
"""
Recherche de fichiers PDF sur mots-clés
"""
def run():
    import re # pour gérer les 'expressions régulières'
    import streamlit as st # pour affichage web
    import requests # pour afficher un fichier par son url
    from io import BytesIO # pour manipuler des flux de données binaires
    import fitz # alias de PyMuPDF, pour manipuler des fichiers pdf 
    from concurrent.futures import ThreadPoolExecutor  # pour exécuter des tâches en parallèle
    import os # pour gérer les répertoires de fichiers
    import tempfile
    import base64
    
    #-----------------------------------------------
    def sup_rep(rep):
        # supprimer les fichiers du répertoire 'rep'
        if os.path.exists(rep):
            for fichier in os.listdir(rep):
                chemin_fichier = os.path.join(rep, fichier)
                if os.path.isfile(chemin_fichier):
                    os.remove(chemin_fichier)  # supprime uniquement les fichiers
        else:
            st.write(f"Le répertoire {rep} n'existe pas")            
                    
    #--------------------------------------------------
    def surligner(chemin,nwl,url,keywords):
        # pour mettre en surbrillance les 'keywords' trouvés dans le fichier 'nwl' d'accès 'url'
        
        #----------------------------------
        def highlight_keywords(pdf_file, keywords, output_path):
            """
            Recherche des mots-clés dans un fichier PDF et les marque en surbrillance.
            
            :param pdf_file: Chemin ou flux du fichier PDF
            :param keywords: Liste des mots-clés à rechercher
            :param output_path: Chemin pour enregistrer le PDF modifié
            """
            with fitz.open(pdf_file) as doc:
                for page in doc:
                    for keyword in keywords:
                        # Recherche les instances du mot-clé dans la page
                        text_instances = page.search_for(keyword)
                        for inst in text_instances:
                            # Ajoute une annotation de surbrillance sur chaque instance trouvée
                            page.add_highlight_annot(inst)
                
                # Enregistre le fichier PDF modifié
                doc.save(output_path, garbage=4, deflate=True)
                
        #----------------------------
    
        response = requests.get(url) # obtention du PDF
        response.raise_for_status()

        # Écrire le fichier PDF en local pour modification
        #with open(chemin + "input.pdf", "wb") as f:
            #f.write(response.content)   
            
        file_path = os.path.join(chemin, "input.pdf")
        st.write(file_path)
        with open(file_path, "wb") as file:
            file.write(response.content)    

        # Marquer les mots-clés et enregistrer le résultat
        # highlight_keywords(chemin + "input.pdf", keywords, chemin + "/output_highlighted_" + nwl + ".pdf")
        highlight_keywords(file_path, keywords, chemin + "/output_highlighted_" + nwl + ".pdf")
        
    #--------------------------------
    def tri_result(results):
        # Tri de 'results' par ordre d'occurrence des mots-clés décroissant
        results_new = []
        for result in results:
            nb_occur = 0 # nombre d'occurrences d'un ou des mots-clé(s) dans le fichier
            for keyword, positions in result['matches'].items(): 
                nb_occur += len(positions)
            # s'il y a au moins une occurrence on crée un élément (dictionnaire) dans la liste 'results_new'  
            # en rajoutant un élément du dictionnaire (nb_occur)
            if nb_occur != 0: 
                url = result['url']
                matches = result['matches']
                nom = result['nom']
                results_new.append({"url": url, "matches": matches,"nom": nom,"nb_occur": nb_occur}) 
        # la liste results_sorted est trié sur la clé 'nb_occur'
        results_sorted = sorted(results_new, key=lambda x: x["nb_occur"], reverse = True)
        return results_sorted   
     
    #--------------------------------
    def manip_url_gdrive(fichier):
        # transformation du lien G-Drive du fichier PDF en une url que 'requests' peut traiter
        resultat = fichier.rsplit("/", 1)[0]  # récupère tout avant le dernier '/' (on enlève 'view?asp=sharing')
        id = resultat.rsplit("/", 1)[1]  # récupère tout après le dernier '/' (c'est à dire l'id)
        resultat = "https://drive.google.com/uc?export=download&id=" + id
        return resultat
            
    # --------------------------------
    def fichiers(noms_fich):
        # affichage des newsletters examinées
        st.markdown("<h4 style='color: blue;'>Newsletters examinées : </h4>", unsafe_allow_html=True) 
        chaine = ', '.join(noms_fich) # transformation de la liste en une chaîne d'éléments séparés par une virgule
        st.markdown(f"<h5 style='color: black;'>{chaine}</h5>", unsafe_allow_html=True)   
    
    # --------------------------------
    def extract_text_fitz(pdf_file):
        # lit le fichier PDF et extrait le texte avec PyMuPDF
        with fitz.open(stream=pdf_file, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
        return text
    
    #---------------------------------------
    def recherche_keywords(text,keywords):
        # recherche des 'keywords' dans 'text''
        results = {}
        for keyword in keywords:
            # m.start() est la position de départ de 'keyword' dans 'text'
            matches = [m.start() for m in re.finditer(keyword, text, re.IGNORECASE)]
            results[keyword]= matches
            
        return results    
    
    #----------------------------------
    def process_file(nom, url, choix, keywords):
        # extraction du texte du fichier'nom' accessiblepar son 'url' et recherche des 'keywords'
        try:
            if choix == "gdrive":
                url_modif = manip_url_gdrive(url)
            else:
                url_modif = url

            response = requests.get(url_modif) # accès au fichier par son url
            response.raise_for_status()
        
            with BytesIO(response.content) as pdf_file:
                # extraction du texte du fichier (hors images)
                text = extract_text_fitz(pdf_file)
            
            # recherche des mots-clés dans le texte
            keyword_matches = recherche_keywords(text, keywords)
            return {"url": url, "matches": keyword_matches, "nom": nom}

        except requests.RequestException as e:
            return {"error": f"erreur téléchargement {url}: {e}"}
        except Exception as e:
            return {"error": f"erreur lecture PDF {url}: {e}"}
    
    #--------------------------------------
    def recherche_in_pdfs(fichiers_nwl, keywords, choix):
        # recherche des mots-clés dans des fichiers PDF accessibles via leurs URLs
        # permet de paralléliser les tâches, ici, chaque fichier PDF est traité dans un thread distinct.
        # cela optimise la performance
        results = []
        with ThreadPoolExecutor() as executor:
            futures = []
            for nom, url in fichiers_nwl.items(): # nom et url d'ne newsletter
                futures.append(executor.submit(process_file, nom, url, choix, keywords))
            for future in futures:
                results.append(future.result())

        return results

    #------------------------------------
    st.markdown("<h2 style='color: black;'>Recherche de Newsletters sur mots-clés</h2>", unsafe_allow_html=True) 
    
    # dictionnaire des url des newsletters
    fichiers_nwl = {

          "NWL90":"https://www.agirabcd.fr/NEWSLETTER/N90/N90_NWL.pdf",        
          "NWL89":"https://www.agirabcd.fr/NEWSLETTER/N89/NWL89.pdf", 
          "NWL88":"https://www.agirabcd.fr/NEWSLETTER/N88/N88-1.pdf", 
          "NWL87":"https://www.agirabcd.fr/NEWSLETTER/N87/NWL_87.pdf", 
          "NWL86":"https://www.agirabcd.fr/NEWSLETTER/N86/N86_NWL.pdf", 
          "NWL85":"https://www.agirabcd.fr/NEWSLETTER/N85/N85_NWL.pdf", 
          "NWL84":"https://www.agirabcd.fr/NEWSLETTER/N84/N84_NWL.pdf", 
          "NWL83":"https://www.agirabcd.fr/NEWSLETTER/N83/83-NWL.pdf", 
          "NWL82":"https://www.agirabcd.fr/NEWSLETTER/N82/82-NWL.pdf", 
          "NWL81":"https://www.agirabcd.fr/NEWSLETTER/N81/81_NWL.pdf", 
          "NWL80":"https://www.agirabcd.fr/NEWSLETTER/N80/80_NWL.pdf"
        
    }
    # chemin d'accès aux fichiers provisoires créés lors de la mise en surbrillance
    #rep_temp = "D:/PDFs/"
    #chemin = "/home/sitebj/www/prov/"  # chez Alwaysdata
    
    # suppression des fichiers du répertoire 'chemin'
    #sup_rep(chemin)
    
    # création d'un répertoire temporaire dans le répertoire système
    chemin = os.path.join(os.getcwd(), "prov")
    os.makedirs(chemin, exist_ok=True)
    st.write(chemin)
    
    # racine de l'URL d'accès au fichier provisoire pdf mis en surbrillance (output_highlighted)
    racine = "https://sitebj.alwaysdata.net/prov/output_highlighted_"
    
    # choix de l'emplacement des fichiers des newsletters ('normal' ou 'gdrive')
    # 'gdrive' dans le cas où les fichiers auraient été copiés dur G-Drive, 
    # 'normal' sinon quand ils sont sur leur emplacement d'origine sur le site AGIRabcd
    choix = "normal"
    
    # affichage de la liste des newsletters examinées
    fichiers(list(fichiers_nwl.keys()))

    # mots-clés recherchés
    st.markdown("<h5 style='color: red;'>Saisir les mots-clés (séparés par des virgules) et cliquer sur 'Afficher résultat recherche'</h5>", unsafe_allow_html=True)
    keywords = st.text_input("Mots-clés (sensible aux accents)")
    keywords = keywords.split(',')  # transformation de la chaîne en liste
    # on supprime les 'blancs' de la liste des mots-clés (utile si rien n'a été saisi)
    while "" in keywords:
        keywords.remove("")
    
    if st.button("Afficher résultat recherche") :
        # à chaque fichier du répertoire correspond un élément de la liste 'results'
        # sous forme d'un dictionnaire constitué du nom du fichier (associé à la clé 'url')
        # et d'un sous-dictionnaire (associé à la clé 'matches') constitué du mot-clé et de la liste des positions du mot-clé
        
        results = recherche_in_pdfs(fichiers_nwl, keywords, choix) # lancement de la recherche
        
        # Tri de 'results' par ordre d'occurrence des mots-clés décroissant
        results_sorted = tri_result(results)
        
        if len(results_sorted) != 0:
            for result in results_sorted:
                # result['matches'] est le dictionnaire constitué d'une clé (keyword) et d'une liste des positions de keyword
                # result['matches'].items() déstructure en 'keyword' et 'positions'
                # len(positions) = nombre d'éléments de la liste donc le nombre d'occurrences de keyword
       
                nwl = result['nom']  # son nom
                url = result['url']  # url de la newsletter
                
                #-----------------------
                # recherche à nouveau des mot-clés et création d'un pdf où les mots-clés trouvés sont surlignés
                surligner(chemin,nwl,url,keywords)
                #url_surlign = racine + nwl +".pdf" # url du fichier PDF surligné
                fich_surlign = chemin + "/output_highlighted_" + nwl + ".pdf"
                st.write(fich_surlign)

                # traitement du fichier output_highlighted
                try:
                    # lecture du fichier pdf
                    with open(fich_surlign, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()
                        
                    # encodage en base64 pour générer un lien HTML    
                    url_surlign = base64.b64encode(pdf_bytes).decode('utf-8')
                    st.write(url_surlign)
                    pdf_link = f'<a href="data:application/pdf;base64,{url_surlign}" target="_blank">Ouvrir le fichier PDF {nwl}</a>'
                    
                    # affichage du lien
                    st.markdown(pdf_link, unsafe_allow_html=True)
                    #st.markdown(f"<h4 style='color: blue;'>Dans le fichier <a href= '{url_surlign}' target='_blank'>{nwl}</a></h4>",unsafe_allow_html=True)
                    #st.markdown(pdf_link, unsafe_allow_html=True)
                except:
                    st.error(f"Le fichier PDF '{fich_surlign}' est introuvable. Vérifiez le chemin.")
                
                #st.markdown(f"<h4 style='color: blue;'>Dans le fichier <a href= '{url_surlign}' target='_blank'>{nwl}</a></h4>",unsafe_allow_html=True)
                for keyword, positions in result['matches'].items(): 
                    if len(positions) != 0:
                        st.markdown(f"<h4 style='color: orange;'>--- le mot-clé '{keyword}' a été trouvé {len(positions)} fois </h4>", unsafe_allow_html=True)
        
        else:
            st.markdown("<h4 style='color: blue;'>aucun mot-clé trouvé dans les newsletters examinées (ou aucun mot-clé saisi)</h4>", unsafe_allow_html=True)
            
# Si l'application est lancée directement (en dehors du portail), lancer l'application
if __name__ == "__main__":    
    run()