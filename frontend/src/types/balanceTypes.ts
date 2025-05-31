// frontend/src/types/balanceTypes.ts

export interface CurrencyRead {
  id: number;
  code: string;
  name: string;
  symbol?: string | null;
}

export interface CurrencyBalance {
  currency: CurrencyRead;
  total_paid: number;
  net_owed_to_user: number;
  net_user_owes: number;
}

export interface UserBalanceResponse {
  balances: CurrencyBalance[];
}
