import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

/** 專案初始化階段的頁面佔位元件，會在各功能完成時被真正的內容取代。 */
export function ComingSoon({ feature }: { feature: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{feature}開發中</CardTitle>
        <CardDescription>這個頁面會在後續開發階段串接 Python FastAPI 後端的真實資料。</CardDescription>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">
        後端 API 文件：<code className="rounded bg-muted px-1.5 py-0.5">http://localhost:8000/docs</code>
      </CardContent>
    </Card>
  );
}
