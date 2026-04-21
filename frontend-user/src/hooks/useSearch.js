import { useQuery } from "@tanstack/react-query";
import { searchHousing } from "../api/housing";
import { useSearchStore } from "../store/searchStore";

export function useSearch() {
  const searchStore = useSearchStore();

  const query = useQuery({
    queryKey: ["housing-search", searchStore.query, searchStore.filters],
    queryFn: () =>
      searchHousing({
        q: searchStore.query,
        ...searchStore.filters,
      }),
  });

  return {
    ...searchStore,
    searchQuery: query,
  };
}

