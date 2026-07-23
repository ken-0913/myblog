---
title: "Go Goroutine 입문 — 동시성을 다루는 가장 작은 단위"
date: 2026-07-20T09:00:00+09:00
draft: false
tags: ["Go", "Golang", "Goroutine", "Concurrency", "동시성"]
categories: ["프로그래밍"]
featuredImage: images/banners/go-goroutine-for-beginners-64aa235c.png
---

**Goroutine**은 Go에서 함수를 동시에 실행하는 가장 작은 단위이다.
Go는 언어 차원에서 동시성(concurrency)을 지원하며, 그 핵심이 Goroutine이다.
이 글은 Goroutine을 처음 접하는 경우를 기준으로 개념과 기본 사용법을 정리한다.

## 동시성(Concurrency)이란

**동시성**은 여러 작업을 번갈아 진행해 마치 함께 처리되는 것처럼 보이게 하는 방식이다.
예를 들어 파일을 내려받으면서 동시에 로그를 출력하는 상황이 이에 해당한다.
하나의 작업이 끝날 때까지 다른 작업이 멈춰 기다리지 않아도 된다는 점이 핵심이다.

일반적인 함수 호출은 **순차적(sequential)**이다.
앞 함수가 끝나야 다음 함수가 실행되므로, 느린 작업이 있으면 전체가 함께 느려진다.
Goroutine은 이 순차 실행을 벗어나 함수를 **동시에** 돌리는 수단이다.

## go 키워드로 시작하기

함수 호출 앞에 **`go`** 키워드만 붙이면 그 함수는 새로운 Goroutine에서 실행된다.
호출한 쪽은 함수가 끝나기를 기다리지 않고 곧바로 다음 줄로 넘어간다.

```go
package main

import (
    "fmt"
    "time"
)

func say(s string) {
    for i := 0; i < 3; i++ {
        fmt.Println(s)
        time.Sleep(100 * time.Millisecond)
    }
}

func main() {
    go say("goroutine") // 새 Goroutine에서 실행
    say("main")         // main Goroutine에서 실행
}
```

`main` 함수 자체도 하나의 Goroutine(**main Goroutine**)에서 돈다.
위 코드는 `say("goroutine")`과 `say("main")`이 서로 번갈아 출력되며 동시에 진행된다.

## main이 먼저 끝나는 문제

Goroutine을 쓸 때 가장 먼저 마주치는 함정이 있다.
**main Goroutine이 끝나면 프로그램 전체가 종료되어, 남은 Goroutine도 함께 사라진다.**

```go
func main() {
    go say("hello")
    // main이 곧바로 끝나면 say는 출력되지 못하고 종료된다
}
```

위 코드는 `hello`가 한 번도 출력되지 않을 수 있다.
`go say("hello")`가 실행될 기회를 얻기 전에 `main`이 끝나버리기 때문이다.
따라서 Goroutine이 끝날 때까지 기다리는 장치가 필요하다.

## sync.WaitGroup으로 기다리기

**`sync.WaitGroup`**은 여러 Goroutine이 모두 끝날 때까지 기다리게 해주는 도구이다.
`Add`로 기다릴 개수를 등록하고, 각 Goroutine이 끝날 때 `Done`을 호출하며, `Wait`로 전부 끝나기를 기다린다.

```go
package main

import (
    "fmt"
    "sync"
)

func worker(id int, wg *sync.WaitGroup) {
    defer wg.Done() // 함수가 끝나면 완료를 알림
    fmt.Printf("worker %d 완료\n", id)
}

func main() {
    var wg sync.WaitGroup

    for i := 1; i <= 3; i++ {
        wg.Add(1) // 기다릴 Goroutine 수를 1 증가
        go worker(i, &wg)
    }

    wg.Wait() // 3개가 모두 끝날 때까지 대기
    fmt.Println("모든 worker 완료")
}
```

`defer wg.Done()`은 함수 종료 시점에 자동으로 완료를 알리므로 실수로 빠뜨릴 위험이 줄어든다.
실행하면 3개의 worker가 모두 끝난 뒤 마지막 줄이 출력된다.

```terminal
$ go run main.go
worker 1 완료
worker 2 완료
worker 3 완료
모든 worker 완료
```

worker의 출력 순서는 실행할 때마다 달라질 수 있다.
동시에 실행되는 Goroutine의 순서는 보장되지 않기 때문이다.

## Goroutine끼리 값 주고받기 — channel

Goroutine은 서로 독립적으로 돌기 때문에 값을 주고받을 통로가 필요하다.
그 통로가 **channel**이며, `make(chan 타입)`으로 생성한다.

```go
package main

import "fmt"

func main() {
    ch := make(chan string)

    go func() {
        ch <- "Goroutine에서 보낸 값" // channel에 값을 넣음(send)
    }()

    msg := <-ch // channel에서 값을 꺼냄(receive)
    fmt.Println(msg)
}
```

`<-` 연산자로 값을 보내고(`ch <- v`) 받는다(`v := <-ch`).
channel은 값이 도착할 때까지 받는 쪽을 자동으로 대기시킨다.
덕분에 `WaitGroup` 없이도 Goroutine의 결과를 안전하게 받아올 수 있다.

## Goroutine이 가벼운 이유

Goroutine은 OS의 **thread**보다 훨씬 가볍다.
thread 하나가 보통 수 MB의 stack을 쓰는 반면, Goroutine은 수 KB에서 시작해 필요할 때 늘어난다.
그래서 수천, 수만 개의 Goroutine을 동시에 띄우는 것도 부담이 크지 않다.

Go 런타임은 다수의 Goroutine을 적은 수의 thread 위에 알아서 배치한다.
개발자는 thread를 직접 관리하지 않고 `go` 키워드만으로 동시성을 표현하면 된다.

## 실전 예제 — Kubernetes는 Goroutine을 이렇게 쓴다

지금까지 배운 세 가지가 실제 코드에서 어떻게 조합되는지 보는 것이 이해에 도움이 된다.
CNCF 프로젝트인 **Kubernetes**의 `client-go` 라이브러리에는 `ParallelizeUntil`이라는 함수가 있다.
**여러 개의 작업을 여러 worker Goroutine에게 나눠 동시에 처리**하는 도구이며, `go func`·`sync.WaitGroup`·channel이 한자리에 등장한다.

아래는 핵심만 간추린 코드이다. (출처: kubernetes/client-go, Apache-2.0)

```go
// 작업(pieces)을 worker 개수만큼의 Goroutine으로 나눠 처리한다
func ParallelizeUntil(workers, pieces int, doWorkPiece func(piece int)) {
    // 1) 처리할 작업 번호를 channel에 모두 넣고 닫는다
    toProcess := make(chan int, pieces)
    for i := 0; i < pieces; i++ {
        toProcess <- i
    }
    close(toProcess)

    // 2) worker 개수만큼 기다리도록 등록
    var wg sync.WaitGroup
    wg.Add(workers)

    for i := 0; i < workers; i++ {
        go func() { // 3) worker를 Goroutine으로 실행
            defer wg.Done() // 끝나면 완료를 통보
            for piece := range toProcess { // 4) channel에서 작업을 하나씩 꺼내 처리
                doWorkPiece(piece)
            }
        }()
    }

    wg.Wait() // 5) 모든 worker가 끝날 때까지 대기
}
```

동작을 **식당 주방**에 비유하면 이해가 쉽다.
처리할 작업들을 통(**channel**)에 쌓아 두고, 요리사 여러 명(**worker Goroutine**)이 통에서 전표를 하나씩 집어 요리한다.
전표가 다 떨어지면 요리사들은 일을 마치고, 매니저는 **모두 끝날 때까지 기다린다**(`wg.Wait`).

이 코드에서 앞서 배운 개념이 각각 어떻게 쓰였는지 정리하면 다음과 같다.

| 배운 개념 | 이 코드에서의 쓰임 |
|---|---|
| `go func()` | worker를 Goroutine으로 띄움 |
| channel | `toProcess`로 작업을 분배하고 `range`로 꺼냄 |
| `sync.WaitGroup` | `Add`/`Done`/`Wait`로 전체 완료를 대기 |

여기서 핵심은 **worker pool**이라는 패턴이다.
worker들이 channel에서 작업을 알아서 하나씩 가져가므로, 누구에게 어떤 작업을 줄지 일일이 정하지 않아도 된다.
Kubernetes의 **scheduler**는 이 함수로 수많은 노드를 동시에 평가해 Pod를 배치할 곳을 빠르게 고른다.

## 자주 하는 실수

**첫째, Goroutine을 띄우고 기다리지 않는 것이다.**
`WaitGroup`이나 channel 없이 `go`만 호출하면 결과를 받기 전에 프로그램이 끝날 수 있다.

**둘째, 여러 Goroutine이 같은 변수를 동시에 수정하는 것이다.**
이 경우 **race condition**이 발생하므로, channel이나 `sync.Mutex`로 접근을 조율해야 한다.
`go run -race` 옵션으로 이러한 문제를 미리 탐지할 수 있다.

## 정리

Goroutine은 `go` 키워드 하나로 함수를 동시에 실행하는 Go의 동시성 단위이다.
main Goroutine이 먼저 끝나지 않도록 `sync.WaitGroup`으로 기다리고, Goroutine 간 값 전달은 channel로 처리한다.
가볍고 다루기 쉬운 만큼, race condition만 주의하면 동시성 코드를 간결하게 작성할 수 있다.
