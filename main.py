from indexer import Indexer

def print_word_index(indexer, index, word):
    print(f"Index for {word}")
    for page_id, positions in index.items():
        print(f"   {indexer.get_link_by_id(page_id)}: (Positions: {positions}, Frequency: {len(positions)})")

def print_query_results(indexer, query, results):
    print(f"Results for query '{query}':")
    if not results:
        print("No results found.")
        return

    sorted_pages = sorted(results.items(), key=lambda x: x[1], reverse=True)
    for page_id, rank in sorted_pages:
        url = indexer.get_link_by_id(page_id)
        print(f"   {url}: (Score: {rank})")


def main():
    indexer = Indexer()
    print("--- Enter a command below ---")

    while True:
        command = input(">>> ").strip().lower().split()


        if command[0] == "build":
            indexer.build_index()
            print("Indexing complete.")

        elif command[0] == "load":
            indexer.load_index()
            print("Index loaded.")

        elif command[0] == "print":
            if indexer.get_if_index_loaded() == False:
                print("Index not loaded. Please load the index first.")
                continue
            if len(command) != 2:
                print("Usage: print <word>")
                continue  
            word = command[1].lower()
            index = indexer.get_word_index(word)
            print_word_index(indexer, index, word)

        elif command[0] == "find":
            if indexer.get_if_index_loaded() == False:
                print("Index not loaded run load to load the index first.")
                continue
            query = " ".join(command[1:])
            results = indexer.find(query)
            print_query_results(indexer, query, results) 
                
if __name__ == "__main__":
    main()  