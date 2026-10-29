"use client";

import { useState } from "react";
import { RotateCcw } from "lucide-react";
import { toast } from "sonner";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button, buttonVariants } from "@/components/ui/button";
import { useRefreshAccountData } from "@/hooks/use-trading";
import { errorMessage } from "@/services/api-client";
import { tradingApi } from "@/services/trading";

export function ResetAccountDialog() {
  const [pending, setPending] = useState(false);
  const refresh = useRefreshAccountData();

  async function reset() {
    setPending(true);
    try {
      const result = await tradingApi.reset();
      toast.success(result.message);
      await refresh();
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setPending(false);
    }
  }

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="outline" size="sm" disabled={pending}>
          <RotateCcw />
          重置模擬帳戶
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>確定要重置模擬帳戶嗎？</AlertDialogTitle>
          <AlertDialogDescription>
            所有持股會被清空，現金回到 NT$ 1,000,000，並開始新的一輪。先前的交易紀錄會保留，可在交易紀錄切換「全部」查看。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>取消</AlertDialogCancel>
          <AlertDialogAction className={buttonVariants({ variant: "destructive" })} onClick={reset}>
            確定重置
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
