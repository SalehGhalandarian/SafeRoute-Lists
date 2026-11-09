// mkgeosite writes an Xray geosite .dat file from plain domain lists.
//
//	mkgeosite -o saferoute.dat CODE=domain:wild.txt,full:exact.txt,keyword:kw.txt [CODE=...]
//
// Each list file has one entry per line. "domain:" entries match the domain
// and all subdomains, "full:" entries match exactly, "keyword:" entries match
// any domain containing the text. Build tool; not shipped.
package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"strings"

	"github.com/xtls/xray-core/app/router"
	"google.golang.org/protobuf/proto"
)

func main() {
	out := flag.String("o", "saferoute.dat", "output file")
	flag.Parse()
	var list router.GeoSiteList
	for _, arg := range flag.Args() {
		code, specs, ok := strings.Cut(arg, "=")
		if !ok {
			fail("bad argument %q", arg)
		}
		site := &router.GeoSite{CountryCode: strings.ToUpper(code)}
		for _, spec := range strings.Split(specs, ",") {
			kind, path, ok := strings.Cut(spec, ":")
			if !ok {
				fail("bad list %q", spec)
			}
			t, known := map[string]router.Domain_Type{"domain": router.Domain_Domain, "full": router.Domain_Full, "keyword": router.Domain_Plain}[kind]
			if !known {
				fail("unknown kind %q", kind)
			}
			f, err := os.Open(path)
			if err != nil {
				fail("%v", err)
			}
			s := bufio.NewScanner(f)
			for s.Scan() {
				if d := strings.TrimSpace(s.Text()); d != "" && !strings.HasPrefix(d, "#") {
					site.Domain = append(site.Domain, &router.Domain{Type: t, Value: d})
				}
			}
			f.Close()
		}
		fmt.Fprintf(os.Stderr, "%s: %d domains\n", site.CountryCode, len(site.Domain))
		list.Entry = append(list.Entry, site)
	}
	b, err := proto.Marshal(&list)
	if err != nil {
		fail("%v", err)
	}
	if err := os.WriteFile(*out, b, 0o644); err != nil {
		fail("%v", err)
	}
}

func fail(f string, a ...any) {
	fmt.Fprintf(os.Stderr, f+"\n", a...)
	os.Exit(1)
}
