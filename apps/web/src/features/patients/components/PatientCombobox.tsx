import * as React from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { Check, ChevronsUpDown, Search } from "lucide-react";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 25;

type Props = {
  value: string;
  onValueChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
};

export function PatientCombobox({
  value,
  onValueChange,
  disabled = false,
  placeholder = "Patient",
}: Props) {
  const clinicId = getClinicId();
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const [debouncedQuery, setDebouncedQuery] = React.useState("");
  const [selectedLabel, setSelectedLabel] = React.useState("");

  React.useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [query]);

  React.useEffect(() => {
    if (!value) setSelectedLabel("");
  }, [value]);

  const patientsQuery = useInfiniteQuery({
    queryKey: ["patients", "picker", clinicId, debouncedQuery],
    queryFn: ({ pageParam }) =>
      api.listPatients({
        q: debouncedQuery || undefined,
        page: pageParam,
        page_size: PAGE_SIZE,
        sort: "name:asc",
      }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const loaded = lastPage.page * lastPage.page_size;
      return loaded < lastPage.total ? lastPage.page + 1 : undefined;
    },
    enabled: open && Boolean(clinicId),
    staleTime: 60_000,
  });

  const patients =
    patientsQuery.data?.pages.flatMap((page) => page.items) ?? [];

  return (
    <Popover
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) setQuery("");
      }}
    >
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn(
            "h-10 w-full justify-between font-normal",
            !value && "text-muted-foreground",
          )}
        >
          <span className="truncate">{selectedLabel || placeholder}</span>
          <ChevronsUpDown className="size-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-[var(--radix-popover-trigger-width)] p-0"
        align="start"
      >
        <div className="relative border-b border-border p-2">
          <Search
            className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden
          />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search patients"
            className="h-9 pl-8"
            autoFocus
          />
        </div>
        <ul
          className="max-h-64 overflow-y-auto p-1"
          role="listbox"
          aria-label="Patients"
          onScroll={(event) => {
            const target = event.currentTarget;
            const nearBottom =
              target.scrollHeight - target.scrollTop - target.clientHeight < 48;
            if (
              nearBottom &&
              patientsQuery.hasNextPage &&
              !patientsQuery.isFetchingNextPage
            ) {
              void patientsQuery.fetchNextPage();
            }
          }}
        >
          {patientsQuery.isLoading ? (
            Array.from({ length: 4 }).map((_, index) => (
              <li
                key={index}
                className="flex min-h-11 items-center gap-2 px-2 py-2"
              >
                <Skeleton className="size-4 shrink-0 rounded" />
                <div className="min-w-0 flex-1">
                  <Skeleton className="h-4 w-36 max-w-full" />
                  <Skeleton className="mt-1 h-3 w-16" />
                </div>
              </li>
            ))
          ) : patients.length === 0 ? (
            <li className="px-3 py-6 text-center text-sm text-muted-foreground">
              No patients found
            </li>
          ) : (
            patients.map((patient) => {
              const active = patient.id === value;
              return (
                <li key={patient.id}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={active}
                    className={cn(
                      "flex min-h-11 w-full cursor-pointer items-center gap-2 rounded-md px-2 py-2 text-left text-sm hover:bg-secondary",
                      active && "bg-secondary",
                    )}
                    onClick={() => {
                      onValueChange(patient.id);
                      setSelectedLabel(patient.full_name);
                      setOpen(false);
                      setQuery("");
                    }}
                  >
                    <Check
                      className={cn(
                        "size-4 shrink-0",
                        active ? "opacity-100" : "opacity-0",
                      )}
                    />
                    <span className="min-w-0">
                      <span className="block truncate">
                        {patient.full_name}
                      </span>
                      <span className="block text-xs text-muted-foreground">
                        #{patient.patient_number}
                      </span>
                    </span>
                  </button>
                </li>
              );
            })
          )}
          {patientsQuery.isFetchingNextPage ? (
            <li className="flex min-h-11 items-center gap-2 px-2 py-2">
              <Skeleton className="size-4 shrink-0 rounded" />
              <div className="min-w-0 flex-1">
                <Skeleton className="h-4 w-32 max-w-full" />
                <Skeleton className="mt-1 h-3 w-14" />
              </div>
              <span className="sr-only">Loading more patients</span>
            </li>
          ) : null}
        </ul>
      </PopoverContent>
    </Popover>
  );
}
