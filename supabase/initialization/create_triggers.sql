--
-- Name: profiles create_org_for_new_user; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER create_org_for_new_user AFTER INSERT ON public.profiles FOR EACH ROW EXECUTE FUNCTION public.create_org_and_map_user();


--
-- Name: profiles handle_null_organization; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER handle_null_organization AFTER INSERT ON public.profiles FOR EACH STATEMENT EXECUTE FUNCTION public.handle_empty_org();

ALTER TABLE public.profiles DISABLE TRIGGER handle_null_organization;


